# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

import os
from utils.merge_request import MergeRequest
import subprocess
import sys


class Config:
    data = {}

    @staticmethod
    def init():
        mr = MergeRequest()
        root_dir = mr.GetRootDirectory()
        config_path = os.path.join(root_dir, "tools_shared.yml")
        if os.path.exists(config_path):
            try:
                import yaml
            except ImportError:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "PyYAML~=6.0"]
                )
                import yaml
            with open(config_path, encoding="utf-8") as config_f:
                Config.data = yaml.load(config_f, Loader=yaml.FullLoader)

    @staticmethod
    def get(key):
        return Config.data.get(key)


if __name__ == "__main__":
    Config.init()
    print(Config.get("FILE_TYPE_CHECKER")["BINARY_FILES_ALLOW_LIST"])
