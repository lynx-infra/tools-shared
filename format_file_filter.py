#!/usr/bin/env python3
# Copyright 2020 The Lynx Authors. All rights reserved.

import re
import sys,os,subprocess
from merge_request import MergeRequest
from config import config
gn_path = 'gn'

# Only check format for following file types.
_FILE_EXTENSIONS = ['.java', '.h', '.hpp', '.c', '.cc', '.cpp', '.m', '.mm', '.ts', '.tsx', '.yml', '.yaml', '.gn', '.gni']
# Commands should be used.
_FORMAT_COMMAND = {
    '.yml': ['npx', '--quiet', '--yes', 'prettier -w'],
    '.yaml': ['npx', '--quiet', '--yes', 'prettier -w'],
    '.ts': ['npx', '--quiet', '--yes', 'prettier -w'],
    '.tsx': ['npx', '--quiet', '--yes', 'prettier -w'],
    '.gn': ['{} format '.format(gn_path)],
    '.gni': ['{} format '.format(gn_path)]
}
__FORMAT_COMMAND_NO_INSTALL = {
  '.yml': 'npx --quiet --no-install prettier',
  '.yaml': 'npx --quiet --no-install prettier',
  '.ts': 'npx --quiet --no-install prettier',
  '.tsx': 'npx --quiet --no-install prettier',
  '.gn': ['{} format '.format(gn_path)],
  '.gni': ['{} format '.format(gn_path)]
}
# Files endsWith these suffixes will not be checked.
_FORBIDDEN_SUFFIXES = ['_jni.h', 'pnpm-lock.yaml', 'Podfile.yml', '.d.ts', '.r.ts']
# Files in these directories will not be checked.
_FORBIDDEN_DIRS = [
  
]

def filterFileExtension(path) :
  for ext in _FILE_EXTENSIONS:
    if path.endswith(ext):
      return True
  return False

def filterSuffix(path):
  for suffix in _FORBIDDEN_SUFFIXES:
    if path.endswith(suffix):
      return False
  return True

def filterPathPrefix(path):
  for dir in _FORBIDDEN_DIRS:
    if re.match(dir, path):
      return False
  return True

def getEndWithNewlineCommand(path):
  return ['tail', '-c1', '<', path, '|', 'read', '-r', '_', '||', 'echo', '>>', path]

def getFormatCommand(path):
  format_command = _FORMAT_COMMAND
  
  # read configuration
  npx_no_install = config.get('npx-no-install')
  if npx_no_install:
    format_command = __FORMAT_COMMAND_NO_INSTALL
  
  for (ext, command) in list(format_command.items()):
    if path.endswith(ext):
      return command + [path] + [';'] + getEndWithNewlineCommand(path)
  # defaults to clang-format
  return ['clang-format', '-i', path] + [';'] + getEndWithNewlineCommand(path)

def shouldFormatFile(path):
  return (filterFileExtension(path)
          and filterSuffix(path)
          and filterPathPrefix(path))

if __name__ == "__main__":
  def testFile(path):
    print(("test for path: " + str(path)))
    print(("filterFileExtension: " + str(filterFileExtension(path))))
    print(("filterSuffix: " + str(filterSuffix(path))))
    print(("filterPathPrefix: " + str(filterPathPrefix(path))))
    print(("shouldFormatFile: " + str(shouldFormatFile(path))))
    print(("getFormatCommand: " + str(getFormatCommand(path))))
    print("")
  testFile("aaa.h")
  testFile("test/B.java")
  testFile("dafdasf.js")
  testFile("Lynx/aaa_jni.h")
  testFile("Lynx/BUILD.gn")
  testFile("Lynx/Lynx.gni")
  testFile("Lynx/third_party/ddd.h")
  testFile("oliver/lynx-kernel/src/index.ts")
  testFile("oliver/lynx-kernel/gulpfile.js")
  testFile("oliver/compiler-ng/src/index.ts")
