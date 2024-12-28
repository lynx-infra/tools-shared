#!/usr/bin/env python3
# Copyright 2020 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.
import inspect
import optparse
import os
import pkgutil

import checkers
import subcommand
import sys
import subprocess

from checkers.checker import Checker, CheckResult
from merge_request import MergeRequest
from config import config


def print_cutting_line(desc="", width=80):
    if desc:
        half_line = "=" * int((width - len(desc) - 2) / 2)
        line = half_line + " " + desc + " " + half_line
        if len(line) < width:
            line = line + "="
    else:
        line = "=" * width
    print(line)


def find_classes(module, is_target=None, handle_error=None, recursive=True):
    classes = set()
    submodules = []
    if not inspect.ismodule(module):
        return classes
    for info, name, is_pkg in pkgutil.iter_modules(module.__path__):
        full_name = module.__name__ + '.' + name
        mod = sys.modules.get(full_name)
        if not mod:
            try:
                mod = info.find_module(full_name).load_module(full_name)
            except AttributeError:
                mod = info.find_spec(full_name).loader.load_module(full_name)
            except Exception as e:
                print(e)
                if handle_error:
                    handle_error(e)
                continue
        if is_pkg and recursive:
            submodules.append(mod)
        else:
            classes = classes.union(
                [
                    c[1]
                    for c in inspect.getmembers(mod, inspect.isclass)
                    if ((is_target is None or is_target(c[1])) and c[1].__module__ == mod.__name__)
                ]
            )
    for m in submodules:
        classes = classes.union(find_classes(m, is_target=is_target, handle_error=handle_error, recursive=recursive))
    return classes


# git lynx build: Run build.
def CMDbuild(parser, args):
    parser.add_option(
        '--ios',
        action='store_true',
        help='Check iOS build.')
    parser.add_option(
        '--android',
        action='store_true',
        help='Check Android build')
    parser.add_option(
        '--unittests',
        action='store_true',
        help='Check unittests build')
    parser.add_option(
        '--encoder-ut',
        action='store_true',
        help='Check encoder ut build')
    parser.add_option(
        '--debug',
        action='store_true',
        help='If --debug, Build debug ut')
    parser.add_option(
        '--enable-relax-tests',
        action='store_true',
        help='Check relax tests build')
    parser.add_option(
        '--asan',
        action='store_true',
        help='run ut on asan mode')
    options, args = parser.parse_args(args)
    mr = MergeRequest()
    root_directory = mr.GetRootDirectory()
    try:
        ci_build_path = os.path.join(root_directory, 'tools', 'ci')
        sys.path.append(ci_build_path)
        from check_android_build import CheckAndroidBuild
        from check_test_build import CheckTestTargetBuild, CheckEncoderUTBuild
    except ImportError as error:
        print(('Import Error: %s' % (error)))
    old_cwd = os.getcwd()
    os.chdir(root_directory)
    try:
        if options.unittests:
            CheckTestTargetBuild(options)
        elif options.encoder_ut:
            CheckEncoderUTBuild(options)
        elif options.android:
            CheckAndroidBuild()
        else:
            print('Error build check: invalid target')
    finally:
        os.chdir(old_cwd)

def CMDcheck(parser, args):
    parser.add_option(
        '--checkers',
        help='Checkers to run, default all',
        default='all'
    )
    parser.add_option(
        '--list',
        action='store_true',
        help='List available checkers'
    )
    parser.add_option(
        '--all',
        action='store_true',
        help='Check all source files in the project.'
    )
    parser.add_option(
        '--changed',
        action='store_true',
        help='Check all changed files'
    )
    parser.add_option(
        '--verbose',
        action='store_true',
        help='Print details'
    )

    options, args = parser.parse_args(args)

    def is_checker(cls):
        return issubclass(cls, Checker) and cls != Checker

    checker_classes = {c.name: c for c in find_classes(checkers, is_checker, recursive=False)}

    if options.list:
        print('Available checkers:')
        print('\n\n'.join('  ' + name + ': ' + cls.help for name, cls in checker_classes.items()))
        return

    mr = MergeRequest()
    if options.all:
        changed_files = mr.GetAllFiles()
    elif options.changed:
        changed_files = mr.GetChangedFiles()
    else:
        changed_files = mr.GetLastCommitFiles()

    if options.verbose:
        print('Changed files:\n  ' + '\n  '.join(changed_files) + '\n')

    # If a user specifies to skip certain check(s) in the commit message, skip local check(s)
    # as well.
    #
    # e.g. adding a "SkipChecks: dependency-check, macros-check" at the end of commit message
    # to skip CQ jobs dependency-check and macros-check as well as local git lynx check of
    # deps and macro.
    log = mr.GetCommitLog().split('\n')
    job_checkers = {
        'coding-style-check': ['coding-style'],
        'commit-check': ['commit-message'],
        'copyright-notice-check': ['copyright'],
        'macros-check': ['macro'],
        'cpplint-check': ['cpplint'],
        'java-lint-check': ['java-lint'],
        'file-type-and-spell-check': ['file-type', 'spell'],
        'deps-permission-check': ['deps-permission'],
        'dependency-check': ['deps'],
        'android-check-style':['android-style'],
    }
    
    
    
    # read configuration
    skipped_checks_of_config = []
    skip_list = config.get('skip')
    if isinstance(skip_list,list):
        skipped_checks_of_config.extend(skip_list)
    
    skipped_checks_of_commit = []
    for line in log:
        if line.startswith("SkipChecks:"):
            skipped_jobs = line.split(':', 1)[1].split(',')
            for job in skipped_jobs:
                skipped_checks_of_commit.extend(job_checkers.get(job.strip(), []))

    if skipped_checks_of_commit:
        print(f'{skipped_checks_of_commit} has been skipped due to commit message.')
    if skipped_checks_of_config:
        print(f'{skipped_checks_of_config} has been skipped due to configuration.')

    # filter checkers
    target_checkers = []
    if options.checkers == "all":
        target_checkers = [c() for c in checker_classes.values() if 
                           c.name not in skipped_checks_of_commit and c.name not in skipped_checks_of_config]
    else:
        checker_names = options.checkers.split(',')
        for name in checker_names:
            if name not in checker_classes:
                raise Exception('Checker ' + name + ' not found')
            target_checkers.append(checker_classes.get(name)())

    old_cwd = os.getcwd()
    os.chdir(mr.GetRootDirectory())
    try:
        for c in target_checkers:
            if options.checkers != "all" and c.name not in options.checkers.split(','):
                continue
            print_cutting_line(c.name)
            res = c.run(options, mr, changed_files)
            print("\n[%s] %s" % (c.name, res))
            print_cutting_line()
            print("")
            if res != CheckResult.PASSED:
                sys.exit(1)
    finally:
        os.chdir(old_cwd)


# git lynx format: Run clang-format for lynx
def CMDformat(parser, args):
    parser.add_option(
        '--all',
        action='store_true',
        help='Format all source files in the project.')
    parser.add_option(
        '--changed',
        action='store_true',
        help='Format all changed files')
    parser.add_option(
        '--verbose',
        action='store_true',
        help='Verbose the process of clang-format.')
    options, args = parser.parse_args(args)
    try:
        import format_file_filter
    except ImportError:
        print('Can not find format_file_filter in the project.')
        return 1
    old_cwd = os.getcwd()
    mr = MergeRequest()
    os.chdir(mr.GetRootDirectory())
    try:
        if options.all:
            changed_files = mr.GetAllFiles()
        elif options.changed:
            changed_files = mr.GetChangedFiles()
        else:
            changed_files = mr.GetLastCommitFiles()
        for filename in changed_files:
            if format_file_filter.shouldFormatFile(filename):
                command = format_file_filter.getFormatCommand(filename)
                output, error = mr.RunCommand(command)
                if error:
                    print(('Error clang-format %s: %s' % (filename, error)))
                    continue
                if options.verbose:
                    print(('Formatting %s: %s' % (filename, output)))
    finally:
        os.chdir(old_cwd)


# git lynx commit:  The encapsulation of [git commit -t (template-file) ],
# the commit message template used is located in /git_templates/normal.
# When editing the commit message, [label], summary, and issue fields are automatically generated .
def CMDcommit(parser, args):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    os.system('git commit -t' + script_dir + '/git_templates/normal')

def CMDhelp(parser, args):
    if not any(i in ('-h', '--help') for i in args):
        args = args + ['--help']
    parser.parse_args(args)
    assert False


class OptionParser(optparse.OptionParser):
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(
            self, *args, prog='git lynx', **kwargs)

    def parse_args(self, args=None, _values=None):
        try:
            return self._parse_args(args)
        finally:
            pass

    def _parse_args(self, args=None):
        # Create an optparse.Values object that will store only the actual passed
        # options, without the defaults.
        actual_options = optparse.Values()
        _, args = optparse.OptionParser.parse_args(self, args, actual_options)
        # Create an optparse.Values object with the default options.
        options = optparse.Values(self.get_default_values().__dict__)
        # Update it with the options passed by the user.
        options._update_careful(actual_options.__dict__)
        return options, args


def main(argv):
    usage = 'git lynx subcommand'
    dispatcher = subcommand.CommandDispatcher(__name__)

    dispatcher.execute(OptionParser(), argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
