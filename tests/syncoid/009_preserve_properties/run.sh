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

zfs create -o recordsize=16k -o xattr=sa -o mountpoint=none -o primarycache=none "${POOL_NAME}"/src
zfs create -V 100M -o volblocksize=8k "${POOL_NAME}"/src/zvol8
zfs create -V 100M -o volblocksize=16k -o primarycache=all "${POOL_NAME}"/src/zvol16
zfs create -V 100M -o volblocksize=64k "${POOL_NAME}"/src/zvol64
zfs create -o recordsize=16k -o primarycache=none "${POOL_NAME}"/src/16
zfs create -o recordsize=32k -o acltype=posixacl "${POOL_NAME}"/src/32
zfs set 'net.openoid:var-name'='with whitespace and !"§$%&/()= symbols' "${POOL_NAME}"/src/32

../../../syncoid --preserve-properties --recursive --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

if [ "$(zfs get -H -o value -t filesystem recordsize "${POOL_NAME}"/dst)" != "16K" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem mountpoint "${POOL_NAME}"/dst)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem xattr "${POOL_NAME}"/dst)" != "sa" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem primarycache "${POOL_NAME}"/dst)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem recordsize "${POOL_NAME}"/dst/16)" != "16K" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem primarycache "${POOL_NAME}"/dst/16)" != "none" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem recordsize "${POOL_NAME}"/dst/32)" != "32K" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem acltype "${POOL_NAME}"/dst/32)" != "posix" ]; then
	exit 1
fi

if [ "$(zfs get -H -o value -t filesystem 'net.openoid:var-name' "${POOL_NAME}"/dst/32)" != "with whitespace and !\"§$%&/()= symbols" ]; then
	exit 1
fi
