# Copyright 2022 The Lynx Authors. All rights reserved.
#!/usr/bin/env python3

import subprocess
import sys
import os

from merge_request import MergeRequest

script_path = os.path.abspath(__file__)
root_dir = os.path.dirname(script_path)

def get_all_rulesets(type):
    path = os.path.join(root_dir,"java-lint-check/rulesets/" + type + "/")
    ret = os.listdir(path)
    return ret

# get command error
def is_cmd_fail(cmd_err_):
    ret = []
    # pmd run.sh no found , fix run.sh or update path of pmd run.sh
    if cmd_err_.find('./run.sh: No such file or directory') != -1 :
        ret.append("Cannot found run.sh, please check java_lint_check.py and fix")

    # pmd ruleset no found , add ruleset or update path of pmd ruleset
    if cmd_err_.find("Cannot load ruleset") != -1:
        ret.append("Cannot load ruleset, please check java_lint_check.py and fix")

    # pmd ruleset has no rules , add check rules to ruleset
    if cmd_err_.find("No rules found") != -1:
        ret.append('No rules found, please check java_lint_check.py and fix')
    return ret

# java lint check on list of files
def JavaLint(files):
    pmd_dir = os.path.join(root_dir,'buildtools/pmd/bin/')
    only_check_rulesets = get_all_rulesets('only_check')
    forbidden_rulesets = get_all_rulesets('forbidden')

    failure_flag = False
    Prohibition = False

    only_check_report = []
    prohibition_report = []
    failure_report = []

    target_files = []
    for f in files:
        if f.endswith(('.java', '.kt')):
            target_files.append(f)
    print(f"log: {target_files}")
    if len(target_files) > 0:
        # use only check rulesets to check files of merge request
        for rule in only_check_rulesets:
            check_rule_path = os.path.join(root_dir,f'java-lint-check/rulesets/only_check/{rule}') 
            cmd = (
                f'{pmd_dir}./run.sh pmd -d {" ".join(target_files)} -f text -R '
                f'{check_rule_path}'
            )
            P = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = P.communicate()
            check_msg = out.decode("utf-8")
            cmd_err = err.decode("utf-8")
            print(f"cmd_err,{cmd_err}")
            if P.returncode!=0 and P.returncode!=4:
                failure_report = is_cmd_fail(cmd_err_=cmd_err)
                failure_flag = True
                break
            
            if len(check_msg) != 0:
                only_check_report.append(check_msg)
                
            if failure_flag:
                break

        if not failure_flag:
            # use forbidden rulesets to check files of merge request
            for rule in forbidden_rulesets:
                forbidden_rule_path = os.path.join(root_dir,f'java-lint-check/rulesets/forbidden/{rule}')
                cmd = (
                    f'{pmd_dir}./run.sh pmd -d {" ".join(target_files)} -f text -R '
                    f'{forbidden_rule_path}'
                )
                P = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = P.communicate()
                check_msg = out.decode("utf-8")
                cmd_err = err.decode("utf-8")

                if P.returncode == 4:
                    Prohibition = True
                elif P.returncode != 4 and P.returncode != 0:
                    failure_report = is_cmd_fail(cmd_err_=cmd_err)
                    failure_flag = True
                    break

                if len(check_msg) != 0:
                    prohibition_report.append(check_msg)

                if failure_flag:
                    break
    print(f"log: {Prohibition}")
    print(f"log: {failure_flag}")
    if not Prohibition and not failure_flag:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('[JavaLint] PASSED')
        if len(only_check_report) >= 1:
            print('WARNING:')
            for msg in only_check_report:
                print(msg)
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        return 0

    # merge request has some prohibitions or command run failed, the returncode should be 1
    else:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('[JavaLint] FAILED')
        if len(failure_report) >= 1:
            print('\nERROR:')
            for msg in failure_report:
                print(msg)
        if len(only_check_report) >= 1:
            print('\nWARNING:')
            for msg in only_check_report:
                print(msg)
        if len(prohibition_report) >= 1:
            print('\nPROHIBITION:')
            for msg in prohibition_report:
                print(msg)
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        return 1

    return 0

# for only java lint check
def main(argv):
    mr = MergeRequest()
    files = []
    files = argv[1]
    print(argv[1])
    if len(argv) >= 2:
        option = argv[1]
    if option == "--all":
        files = mr.GetAllFiles()
    elif option == "--changed":
        files = mr.GetChangedFiles()
    else :
        files = mr.GetLastCommitFiles()
    return JavaLint(files)

if __name__ == "__main__":
    sys.exit(main(sys.argv))