#!/bin/bash

# test replication with fallback to bookmarks and all intermediate snapshots

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-2.zpool"
POOL_SIZE="200M"
POOL_NAME="syncoid-test-2"
TARGET_CHECKSUM="2460d4d4417793d2c7a5c72cbea4a8a584c0064bf48d8b6daa8ba55076cba66d  -"

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

# create intermediate snapshots
# sleep is needed so creation time can be used for proper sorting
sleep 1
zfs snapshot "${POOL_NAME}"/src@snap2
sleep 1
zfs snapshot "${POOL_NAME}"/src@snap3
sleep 1
zfs snapshot "${POOL_NAME}"/src@snap4
sleep 1
zfs snapshot "${POOL_NAME}"/src@snap5

# replicate which should fallback to bookmarks
../../../syncoid --no-stream --no-sync-snap --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst || exit 1

# verify
output=$(zfs list -t snapshot -r "${POOL_NAME}" -H -o name)
checksum=$(echo "${output}" | sha256sum)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
	exit 1
fi

exit 0
