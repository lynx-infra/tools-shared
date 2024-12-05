import sys

import code_format_helper
import format_file_filter
from checkers.checker import Checker, CheckResult
from process_header_path_helper import shouldProcessIncludeHeader, findSearchDirs


class CodingStyleChecker(Checker):
    name = 'coding-style'
    help = 'Check coding style'

    def run(self, options, mr, changed_files):
        failed_path = []
        print('Checking file format.')
        header_search_dirs = findSearchDirs()
        for filename in changed_files:
            if format_file_filter.shouldFormatFile(filename):
                if not code_format_helper.check_format(filename) or shouldProcessIncludeHeader(filename, header_search_dirs):
                    failed_path.append(filename)
        if len(failed_path) > 0:
            print("The following file(s) do not satisfy `clang-format` or `prettier`!")
            for filename in failed_path:
                print(filename)
            return CheckResult.FAILED
        else:
            return CheckResult.PASSED
