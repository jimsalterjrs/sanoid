#!/bin/bash

# test using bookmark created after last snapshot

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-015.zpool"
MOUNT_TARGET="/tmp/syncoid-test-015.mount"
POOL_SIZE="1000M"
POOL_NAME="syncoid-test-015"
TARGET_CHECKSUM="73d7271f58f0d79eea0dd69d5ee3f4fe3aeaa3cb8106f7fc88feded5be3ce04e  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m "${MOUNT_TARGET}" -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/a
zfs snapshot "${POOL_NAME}"/a@s0

# This fully replicates a to b
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

echo "Test 1" > "${MOUNT_TARGET}"/a/file1
zfs snapshot "${POOL_NAME}"/a@s1

# This incrementally replicates from a@s0 to a@s1
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

echo "Test 2" > "${MOUNT_TARGET}"/a/file2
zfs snapshot "${POOL_NAME}"/a@s2

# Destroy latest common snap between a and b
zfs destroy "${POOL_NAME}"/a@s1

# This uses a#s1 as base snap although common but older snap a@s0 exists
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

echo "Test 3" > "${MOUNT_TARGET}"/a/file3
zfs snapshot "${POOL_NAME}"/a@s3

# This uses a@s2 as base snap again
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

# verify
output=$(zfs list -t snapshot -r -H -o name "${POOL_NAME}")
checksum=$(echo "${output}" | shasum -a 256)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
  exit 1
fi

exit 0
