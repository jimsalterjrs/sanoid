#!/bin/bash

# test preserving the recordsize from the src filesystem to the target one

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-7.zpool"
MOUNT_TARGET="/tmp/syncoid-test-7.mount"
POOL_SIZE="1000M"
POOL_NAME="syncoid-test-7"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
zfs create -V 100M -o volblocksize=4k "${POOL_NAME}"/src/zvol4
zfs create -V 100M -o volblocksize=16k "${POOL_NAME}"/src/zvol16
zfs create -V 100M -o volblocksize=64k "${POOL_NAME}"/src/zvol64
zfs create -o recordsize=16k "${POOL_NAME}"/src/16
zfs create -o recordsize=32k "${POOL_NAME}"/src/32
zfs create -o recordsize=128k "${POOL_NAME}"/src/128
../../../syncoid --preserve-recordsize --recursive --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

zfs get recordsize -t filesystem -r "${POOL_NAME}"/dst
zfs get volblocksize -t volume -r "${POOL_NAME}"/dst

if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst/16)" != "16K" ]; then
	exit 1
fi

if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst/32)" != "32K" ]; then
	exit 1
fi

if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst/128)" != "128K" ]; then
	exit 1
fi
