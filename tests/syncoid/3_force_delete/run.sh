#!/bin/bash

# test replication with deletion of target if no matches are found

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-3.zpool"
POOL_SIZE="200M"
POOL_NAME="syncoid-test-3"
TARGET_CHECKSUM="0409a2ac216e69971270817189cef7caa91f6306fad9eab1033955b7e7c6bd4c  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
zfs create "${POOL_NAME}"/src/1
zfs create "${POOL_NAME}"/src/2
zfs create "${POOL_NAME}"/src/3

# initial replication
../../../syncoid -r --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst
# destroy last common snapshot on source
zfs destroy "${POOL_NAME}"/src/2@%
zfs snapshot "${POOL_NAME}"/src/2@test
sleep 1
../../../syncoid -r --force-delete --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst || exit 1

# verify
output=$(zfs list -t snapshot -r "${POOL_NAME}" -H -o name | sed 's/@syncoid_.*$'/@syncoid_/)
checksum=$(echo "${output}" | sha256sum)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
	exit 1
fi

exit 0
