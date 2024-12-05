#!/usr/bin/env python3
# Copyright 2022 The Lynx Authors. All rights reserved.

from argparse import Namespace

from cocoapods.downloaders.downloader import Downloader
from cocoapods.sources import ExternalSource


class ExternalDownloader(Downloader):
    type = None

    @classmethod
    def matched(cls, source):
        return isinstance(source, ExternalSource)

    @classmethod
    def download(
        cls, source: dict, root_dir: str, target_dir: str = None, name: str = None, options: Namespace = None,
        cache_dir: str = None
    ):
        pass
