# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import checkers
import os
import sys
from config import Config
from checkers.checker import Checker
from utils.find_classes import find_classes


def is_checker(cls):
    return issubclass(cls, Checker) and cls != Checker


class CheckerManager:
    def __init__(self, ignore):
        self.checker_classes = {
            c.name: c for c in find_classes(checkers, is_checker, recursive=False)
        }

        self.load_external_checker()
        self.remove_ignore_checker(ignore)

    def remove_ignore_checker(self, ignore):
        old_checker_class = self.checker_classes
        self.checker_classes = {
            name: cls
            for name, cls in old_checker_class.items()
            if name not in ignore.split(",")
        }

    def load_external_checker(self):
        external_checker_path = Config.get("external_checker_path")
        if external_checker_path is None:
            return
        abs_dir_path = os.path.abspath(external_checker_path)
        if not os.path.isdir(abs_dir_path):
            raise NotADirectoryError(f"The path {abs_dir_path} is not a directory.")
        sys.path.insert(0, abs_dir_path)
        try:
            import external_checkers

            classes = find_classes(external_checkers, is_checker, recursive=False)
            for c in classes:
                self.checker_classes[c.name] = c
        except Exception as e:
            print(f"Import external checker error {e}")


if __name__ == "__main__":
    Config.init()
    CheckerManager()
