#!/bin/bash

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
python3 $BASEDIR/envsetup.py "$@"

pushd $BASEDIR > /dev/null
$BASEDIR/lcm sync
popd > /dev/null