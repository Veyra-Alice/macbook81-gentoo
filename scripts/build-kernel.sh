#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Compile only. Never installs on the running host or writes a block device.
set -euo pipefail
if [[ $# != 2 ]]; then
    echo "Usage: $0 PREPARED_SOURCE CONFIGURED_OUTPUT" >&2
    exit 2
fi
project=$(cd -- "$(dirname -- "$0")/.." && pwd)
source_dir=$(realpath -- "$1")
output_dir=$(realpath -- "$2")
# Keep build-host identity and wall-clock time out of the kernel banner.
export KBUILD_BUILD_USER=builder
export KBUILD_BUILD_HOST=macbook81
export KBUILD_BUILD_TIMESTAMP='Mon Nov 23 00:00:00 UTC 2026'
export KBUILD_BUILD_VERSION=1
export SOURCE_DATE_EPOCH=1795392000
[[ -f $source_dir/macbook81-source-receipt.json && -f $output_dir/config-report.json ]]
[[ $(id -u) != 0 ]] || { echo 'Compile as an ordinary user.' >&2; exit 1; }
make -C "$source_dir" O="$output_dir" -j"${JOBS:-8}" bzImage modules
# Build external EC wake and FaceTime camera sources against this exact ABI.
mkdir -p "$output_dir/external/ec-wake"
cp "$project/kernel/ec-wake/"* "$output_dir/external/ec-wake/"
make -C "$output_dir" M="$output_dir/external/ec-wake" -j"${JOBS:-8}" modules
if [[ -n ${FACETIMEHD_SOURCE:-} ]]; then
    camera_source=$(realpath -- "$FACETIMEHD_SOURCE")
    camera_commit=4159eef064e4170cbd94fd6c633cbd04bf589c4d
    [[ $(git -C "$camera_source" rev-parse HEAD) == "$camera_commit" ]]
    mkdir -p "$output_dir/external/facetimehd"
    git -C "$camera_source" archive "$camera_commit" | tar -x -C "$output_dir/external/facetimehd"
    make -C "$output_dir" M="$output_dir/external/facetimehd" -j"${JOBS:-8}" modules
else
    echo 'Set FACETIMEHD_SOURCE to the pinned checkout to build the camera module.' >&2
fi
make -C "$source_dir" O="$output_dir" -j"${JOBS:-8}" INSTALL_MOD_PATH="$output_dir/modules" INSTALL_MOD_STRIP=1 modules_install
version=$(make -s -C "$source_dir" O="$output_dir" kernelrelease)
install -D -m 644 "$output_dir/external/ec-wake/macbook81_ec_wake.ko" "$output_dir/modules/lib/modules/$version/extra/macbook81_ec_wake.ko"
if [[ -f $output_dir/external/facetimehd/facetimehd.ko ]]; then
    install -D -m 644 "$output_dir/external/facetimehd/facetimehd.ko" "$output_dir/modules/lib/modules/$version/extra/facetimehd.ko"
fi
depmod -b "$output_dir/modules" "$version"
printf 'Built %s in %s. Nothing has been installed on this host.\n' "$version" "$output_dir"
