#!/bin/bash

# test replication with deletion of conflicting snapshot on target

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-8.zpool"
POOL_SIZE="200M"
POOL_NAME="syncoid-test-8"
TARGET_CHECKSUM="ee439200c9fa54fc33ce301ef64d4240a6c5587766bfeb651c5cf358e11ec89d  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
zfs snapshot "${POOL_NAME}"/src@duplicate

# initial replication
../../../syncoid -r --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst
# recreate snapshot with the same name on src
zfs destroy "${POOL_NAME}"/src@duplicate
zfs snapshot "${POOL_NAME}"/src@duplicate
sleep 1
../../../syncoid -r --force-delete --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst || exit 1

# verify
output1=$(zfs list -t snapshot -r -H -o guid,name "${POOL_NAME}"/src | sed 's/@syncoid_.*$'/@syncoid_/)
checksum1=$(echo "${output1}" | shasum -a 256)

output2=$(zfs list -t snapshot -r -H -o guid,name "${POOL_NAME}"/dst | sed 's/@syncoid_.*$'/@syncoid_/ | sed 's/dst/src/')
checksum2=$(echo "${output2}" | shasum -a 256)

if [ "${checksum1}" != "${checksum2}" ]; then
	exit 1
fi

exit 0
