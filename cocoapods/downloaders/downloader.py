#!/usr/bin/env python3
# Copyright 2022 The Lynx Authors. All rights reserved.

from abc import ABC
from argparse import Namespace


class Downloader(ABC):
    type = None

    @classmethod
    def matched(cls, spec):
        return cls.type in spec.source

    @classmethod
    def download(
        cls, source: dict, root_dir: str, target_dir: str = None, name: str = None, options: Namespace = None,
        cache_dir: str = None
    ):
        raise NotImplementedError
