#!/usr/bin/env python3
# Copyright 2022 The Lynx Authors. All rights reserved.


class Raw:
    pass


class StringList:
    pass


class Rebase:

    def __init__(self, path, base):
        self.path = path
        self.base = base
