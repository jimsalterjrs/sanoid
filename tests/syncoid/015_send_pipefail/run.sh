#!/bin/bash
# test replication pipeline failure in zfs send 

set -eux

. ../../common/lib.sh

POOL_NAME="syncoid-test-013"
POOL_IMAGE="/tmp/${POOL_NAME}.zpool"
POOL_KEY="/tmp/${POOL_NAME}.key"
POOL_SIZE="200M"
TARGET_CHECKSUM="ec45c5a4b7c9557b351cb485904cd310561505f41fe8a48da55eab9419a82bdb  -"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
  rm -f "${POOL_IMAGE}" "${POOL_KEY}"
}
trap cleanUp EXIT # export pool in any case

echo "${POOL_NAME}" > "${POOL_KEY}"
zfs create -o encryption=on -o keyformat=passphrase -o keylocation=file://"${POOL_KEY}" "${POOL_NAME}"/src

# initial replication
zfs snapshot "${POOL_NAME}"/src@snap1
../../../syncoid --debug --no-sync-snap "${POOL_NAME}"/src "${POOL_NAME}"/dst

# break the source
zfs unload-key "${POOL_NAME}/src"

# zfs send must fail because source is unreadable
zfs snapshot "${POOL_NAME}"/src@snap2
if ../../../syncoid --debug --no-sync-snap "${POOL_NAME}"/src "${POOL_NAME}"/dst; then
  echo "syncoid succeeded against unreadable source" >&2
  exit 1
fi

# verify
output=$(zfs list -t snapshot -r -H -o name "${POOL_NAME}")
checksum=$(echo "${output}" | grep -v syncoid_ | shasum -a 256)

if [ "${checksum}" != "${TARGET_CHECKSUM}" ]; then
	exit 1
fi

exit 0
