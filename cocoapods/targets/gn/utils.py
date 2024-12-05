#!/usr/bin/env python3
# Copyright 2022 The Lynx Authors. All rights reserved.

from cocoapods.targets.gn.base_target import BaseTarget
from cocoapods.targets.gn.bundle_data import BundleData
from cocoapods.targets.gn.config import Config
from cocoapods.targets.gn.group import Group
from cocoapods.targets.gn.shared_library import SharedLibrary

TARGETS = {
    'source_set': BaseTarget,
    'config': Config,
    'group': Group,
    'bundle_data': BundleData,
    'shared_library': SharedLibrary,
}


def create_target(type_, name):
    return TARGETS[type_](name)
