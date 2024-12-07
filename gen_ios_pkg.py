#!/usr/bin/env python
# Copyright 2024 The Lynx Authors
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import os
import sys
import json
import shutil
import subprocess
from cocoapods.specification import Specification
from cocoapods.pod import Pod


def run_command(command):
    # When the "command" is a multi-line command, only the status of the last line of the command is checked.
    # Therefore, it is necessary to add "set -e" to ensure that any error in any line of the command will cause the script to exit immediately.
    command = 'set -e\n' + command

    print(f'run command: {command}')
    res = subprocess.run(['bash', '-c', command], stderr=subprocess.STDOUT, check=True, text=True)

def replace_vmsdk_version(version):
    lines = []
    with open('monitor/VmsdkVersion.m', 'r') as f:
        lines = f.readlines()
    with open('monitor/VmsdkVersion.m', 'w') as f:
        for line in lines:
            if '#define VMSDK_POD_VERSION' in line:
                f.write(f'#define VMSDK_POD_VERSION @"9999_{version}"\n')
            else:
                f.write(f'{line}')

def copy_and_generate_podspec(repo_name):
    print('run copy_and_generate_podspec')
    shutil.copyfile(f'Darwin/iOS/podspec_templates/{repo_name}.podspec',
                    f'{repo_name}.podspec')
    run_command(f'export LYNX_LCM_SYNC_EXECUTED=1')
    run_command(f'tools/lynx_tools/lcm sync --no-history --target ios')
    run_command(f'python3 tools/ios_tools/generate_ios_podspec_by_gn.py --target {repo_name}')

def change_podspec_and_get_source_files(repo_name):
    print('run generate_podspec')
    run_command('pwd')
    run_command(f'bundle exec pod ipc spec {repo_name}.podspec > {repo_name}.podspec.json')
    content = None
    with open(f'{repo_name}.podspec.json', 'r') as f:
        content = json.load(f)

    if 'prepare_command' in content and content['prepare_command'] != '':
        prepare_command = content['prepare_command']
        run_command(prepare_command)

    # use the newly generated podspec
    run_command(f'bundle exec pod ipc spec {repo_name}.podspec > {repo_name}.podspec.json')
    with open(f'{repo_name}.podspec.json', 'r') as f:
        content = json.load(f)

    content['prepare_command'] = ''
    with open(f'{repo_name}.podspec.json', 'w') as f:
        json.dump(content, f, indent=4)

    # get the source file name by using the Specification

    pod = Pod(name='', version='', source=None)
    # only need use pod.target_dir
    pod._target_dir=''

    spec = Specification(pod,None,content)
    files = spec._files_accessor.get_all_files()
    return files

def delete_useless_files(source_files,repo_name,source_dirs):
    """
        @source_files:  source files need to be preserved
        @repo_name: name of repository
        @source_dirs: additional dirs need to be preserved
    """
    print("run delete_useless_files")
    current_directory = os.getcwd()
    source_files = [os.path.join(current_directory,file_name) for file_name in source_files]
    source_dirs_list = [os.path.join(current_directory, dir_item) for dir_item in source_dirs]
    for root, dirnames, filenames in os.walk(current_directory):
        if root in source_dirs_list:
            continue
        for dirname in dirnames:
            if os.path.islink(os.path.join(root, dirname)) :
                os.unlink(os.path.join(root, dirname))
        for file_name in filenames:
            file_name = os.path.join(root, file_name)
            if file_name not in source_files:
                base_name = os.path.basename(file_name)
                if base_name != f"{repo_name}.podspec" and base_name != f"{repo_name}.podspec.json":
                    os.remove(file_name)

    run_command('find . -type d -empty -delete')

def main(argv):
    package_env = argv[0]
    print(f"run in {package_env} environment")
    repo_name = argv[1]
    if not repo_name and package_env=='prod':
        repo_name = os.environ.get('repo_name') or os.environ.get('repoName')
    print(f"repo_name: {repo_name}")


    source_dirs = ['build']
    # copy_and_generate_podspec(repo_name)
    source_files = change_podspec_and_get_source_files(repo_name)
    delete_useless_files(source_files,repo_name,source_dirs)

if __name__ == '__main__':    
    sys.exit(main(sys.argv[1:]))
