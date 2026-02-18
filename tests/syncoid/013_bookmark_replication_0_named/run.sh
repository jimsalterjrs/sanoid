#!/bin/bash

# test replication with fallback to bookmarks and special named snapshot/bookmark '0'

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-013.zpool"
POOL_SIZE="200M"
POOL_NAME="syncoid-test-013"
TARGET_CHECKSUM="b927125d2113c8da1a7f0181516e8f57fee5d268bdd5386d6ff7ddf31d6d6a35  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
zfs snapshot "${POOL_NAME}"/src@0

# initial replication
../../../syncoid --no-sync-snap --create-bookmark --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

# destroy last common snapshot on source
zfs destroy "${POOL_NAME}"/src@0

zfs snapshot "${POOL_NAME}"/src@1

# replicate which should fallback to bookmarks
../../../syncoid --no-sync-snap --create-bookmark --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

# verify
output=$(zfs list -t snapshot -r -H -o name "${POOL_NAME}"; zfs list -t bookmark -r -H -o name "${POOL_NAME}")
checksum=$(echo "${output}" | grep -v syncoid_ | shasum -a 256)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
	exit 1
fi

exit 0
