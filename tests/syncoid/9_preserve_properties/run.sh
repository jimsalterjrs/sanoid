#!/bin/bash

# test preserving locally set properties from the src dataset to the target one

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-9.zpool"
MOUNT_TARGET="/tmp/syncoid-test-9.mount"
POOL_SIZE="1000M"
POOL_NAME="syncoid-test-9"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create -o recordsize=16k -o xattr=on -o mountpoint=none -o primarycache=none "${POOL_NAME}"/src
zfs create -V 100M -o volblocksize=8k "${POOL_NAME}"/src/zvol8
zfs create -V 100M -o volblocksize=16k -o primarycache=all "${POOL_NAME}"/src/zvol16
zfs create -V 100M -o volblocksize=64k "${POOL_NAME}"/src/zvol64
zfs create -o recordsize=16k -o primarycache=none "${POOL_NAME}"/src/16
zfs create -o recordsize=32k -o acltype=posixacl "${POOL_NAME}"/src/32

../../../syncoid --preserve-properties --recursive --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst


if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst)" != "16K" ]; then
	exit 1
fi

if [ "$(zfs get mountpoint -H -o value -t filesystem "${POOL_NAME}"/dst)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get xattr -H -o value -t filesystem "${POOL_NAME}"/dst)" != "on" ]; then
	exit 1
fi

if [ "$(zfs get primarycache -H -o value -t filesystem "${POOL_NAME}"/dst)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst/16)" != "16K" ]; then
	exit 1
fi

if [ "$(zfs get primarycache -H -o value -t filesystem "${POOL_NAME}"/dst/16)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get recordsize -H -o value -t filesystem "${POOL_NAME}"/dst/32)" != "32K" ]; then
	exit 1
fi

if [ "$(zfs get acltype -H -o value -t filesystem "${POOL_NAME}"/dst/32)" != "posix" ]; then
	exit 1
fi
