#!/bin/bash
# Copyright 2024 The Lynx Authors. All rights reserved.
# Licensed under the Apache License Version 2.0 that can be found in the
# LICENSE file in the root directory of this source tree.

if [[ -n "${BASH_SOURCE[0]}" ]]; then
    # Bash shell
    BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [[ -n "$ZSH_VERSION" ]]; then
    # ZSH shell
    BASEDIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
else
    echo "Unsupported shell"
    exit 1
fi

# NPM configuration
export NPM_CONFIG_UPDATE_NOTIFIER=false

export BUILDTOOLS_DIR="${BASEDIR}/buildtools"
export PATH=$BASEDIR:${BUILDTOOLS_DIR}/clang-format:${BUILDTOOLS_DIR}/gn:${BUILDTOOLS_DIR}/node/bin:$PATH
