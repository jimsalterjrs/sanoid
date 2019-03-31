#!/bin/bash

# test replication edge cases with bookmarks

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-4.zpool"
POOL_SIZE="200M"
POOL_NAME="syncoid-test-4"
TARGET_CHECKSUM="ad383b157b01635ddcf13612ac55577ad9c8dcf3fbfc9eb91792e27ec8db739b  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
zfs snapshot "${POOL_NAME}"/src@snap1
zfs bookmark "${POOL_NAME}"/src@snap1 "${POOL_NAME}"/src#snap1
# initial replication
../../../syncoid --no-sync-snap --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst
# destroy last common snapshot on source
zfs destroy "${POOL_NAME}"/src@snap1
zfs snapshot "${POOL_NAME}"/src@snap2

# replicate which should fallback to bookmarks and stop because it's already on the latest snapshot
../../../syncoid --no-sync-snap --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst || exit 1

# verify
output=$(zfs list -t snapshot -r -H -o name "${POOL_NAME}")
checksum=$(echo "${output}" | grep -v syncoid_ | shasum -a 256)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
	exit 1
fi

exit 0
