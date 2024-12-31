#!/usr/bin/env python
# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import os
import sys
import json
import argparse
import subprocess
from cocoapods.specification import Specification
from cocoapods.pod import Pod
import re
import shutil

target_dir = 'source_package'

def run_command(command):
    # When the "command" is a multi-line command, only the status of the last line of the command is checked.
    # Therefore, it is necessary to add "set -e" to ensure that any error in any line of the command will cause the script to exit immediately.
    command = 'set -e\n' + command

    print(f'run command: {command}')
    res = subprocess.run(['bash', '-c', command], stderr=subprocess.STDOUT, check=True, text=True)

def change_podspec_and_get_source_files(repo_name):
    print('run generate_podspec')
    run_command(f'bundle install --path ./bundle/')
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
                if base_name != f"{repo_name}.podspec" and base_name != f"{repo_name}.podspec.json" and base_name != "LICENSE":
                    os.remove(file_name)

    run_command('find . -type d -empty -delete')
    
def copy_to_target_folder(source_files,repo_name,source_dirs):
    """
        @source_files:  source files need to be preserved
        @repo_name: name of repository
        @source_dirs: additional dirs need to be preserved
    """
    run_command(f'mkdir {target_dir}')
    print("copy files to target directory")
    current_directory = os.getcwd()
    source_files = [os.path.join(current_directory,file_name) for file_name in source_files]
    source_dirs_list = [os.path.join(current_directory,'.github')]
    for root, dirnames, filenames in os.walk(current_directory):
        # exclude target file in os.walk
        dirnames[:] = [d for d in dirnames if d != target_dir]
        
        if root in source_dirs_list:
            relative_dir_path = os.path.relpath(root, current_directory)
            target_dir_path = os.path.join(target_dir,relative_dir_path)
            shutil.copytree(relative_dir_path, target_dir_path)
            
        for file_name in filenames:
            complete_file_name = os.path.join(root, file_name)
            if complete_file_name in source_files or file_name == f"{repo_name}.podspec" or file_name == f"{repo_name}.podspec.json" \
                or (file_name == "LICENSE" and root==current_directory):
                relative_path =  os.path.relpath(complete_file_name, current_directory)
                target_path = os.path.join(target_dir,relative_path)
                
                # create the directory
                destination_dir = os.path.dirname(target_path)  
                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)  
                shutil.copyfile(relative_path,os.path.join(target_dir,relative_path))
                continue
    
def replace_source_of_podspec(repo_name,tag):
    # only for github
    content = None
    with open(f'{repo_name}.podspec', 'r') as f:
        content = f.read()
    
    pattern = "s.source\s?=\s?{.*?}"
    source_code_repo = os.environ.get('GITHUB_REPOSITORY')
    ref = os.environ.get('GITHUB_REF')
    if ref:
        ref= ref.replace("refs/tags/","")
    target_string=f's.source = {{ :http =>  "https://github.com/{source_code_repo}/releases/download/{tag}/{repo_name}.zip" }}'
    new_content = re.sub(pattern, target_string, content)
    # update the podspec
    with open(f'{repo_name}.podspec', 'w') as f:
        f.write(new_content)
        
    run_command(f'bundle exec pod ipc spec {repo_name}.podspec > {repo_name}.podspec.json')

def main():
    parser = argparse.ArgumentParser(description='Generate a iOS source code zip')
    parser.add_argument('--env', type=str, help='Path to the private PEM file', required=True)
    parser.add_argument('--replace_source', action="store_true", help='Replace the source of podspec')
    parser.add_argument('--repo', type=str, help='Replace the source of podspec')
    parser.add_argument('--delete',action="store_true",help='Whether to delete files other than the source code package')
    parser.add_argument('--tag',type=str,help='The tag of pod')
    parser.add_argument('--package_dir',type=str,help='The root dir of package')
    args = parser.parse_args()
  
    package_env = args.env
    print(f"run in {package_env} environment")
    repo_name = args.repo
    if not repo_name and package_env=='prod':
        repo_name = os.environ.get('repo_name') or os.environ.get('repoName')
    print(f"repo_name: {repo_name}")


    source_dirs = ['build']
    source_files = change_podspec_and_get_source_files(repo_name)
    
    if args.delete:
        delete_useless_files(source_files,repo_name,source_dirs)
    else:
        copy_to_target_folder(source_files,repo_name,source_dirs)
        
    if args.replace_source:
        # replace the source of podspec
        print("start replacing source of podspec")
        replace_source_of_podspec(repo_name, args.tag)
        
    # get the zip package
    if not args.delete:
        if args.package_dir:
            # move all files under package_dir
            tmp_dir = 'tmp_dir'
            run_command(f'mkdir ${tmp_dir}')
            run_command(f'mv {target_dir}/* {tmp_dir}')
            # move hidden files
            run_command(f'mv {target_dir}/.* {tmp_dir}')
            
            run_command(f'mkdir {target_dir}/{args.package_dir}')
            run_command(f'mkdir {tmp_dir}/* {target_dir}')
            run_command(f'mkdir {tmp_dir}/.* {target_dir}')
        else:
            run_command(f'cd {target_dir} && zip -r ../{repo_name}.zip * -x "*.zip"')
    else:
        run_command(f'zip -r {repo_name}.zip * -x "*.zip"')


if __name__ == '__main__':    
    sys.exit(main())
