# Copyright 2022 The Lynx Authors. All rights reserved.
import java_lint_check
from checkers.checker import Checker, CheckResult


class CpplintChecker(Checker):
    name = 'java-lint'
    help = 'Run java lint'

    def run(self, options, mr, changed_files):
        returncode = java_lint_check.JavaLint(changed_files)
        if returncode == 1:
            return CheckResult.FAILED
        else:
            return CheckResult.PASSED