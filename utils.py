# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.
import subprocess
import fnmatch
import sys


def git_root_dir(path=None):
    command = ["git", "rev-parse", "--show-toplevel"]
    p = subprocess.Popen(
        " ".join(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=path,
    )
    result, error = p.communicate()
    if error:
        raise Exception(
            "Error, can not get top directory, make sure it is a git repo: %s"
            % (error.decode("utf-8"))
        )
    return result.decode("utf-8").strip()


def match_globs(target, patterns):
    for p in patterns:
        if fnmatch.fnmatch(target, p):
            return True
    return False


def is_mac():
    return sys.platform == "darwin"


def is_win():
    return sys.platform.startswith(("cygwin", "win"))


def is_linux64():
    return sys.platform.startswith("linux")


def read_file(path):
    with open(path, "r") as f:
        return f.read()
