#!/bin/bash

# test if guid of existing bookmark matches new guid

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-014.zpool"
MOUNT_TARGET="/tmp/syncoid-test-014.mount"
POOL_SIZE="1000M"
POOL_NAME="syncoid-test-014"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m "${MOUNT_TARGET}" -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

function getGuid {
  zfs get -H guid "$1" | awk '{print $3}'
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}/a"
zfs snapshot "${POOL_NAME}/a@s0"

# This fully replicates a to b
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

# This fully replicates a to c
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/c

bookmark_guid=$(getGuid "${POOL_NAME}/a#s0")
snap_a_guid=$(getGuid "${POOL_NAME}/a@s0")
snap_b_guid=$(getGuid "${POOL_NAME}/b@s0")
snap_c_guid=$(getGuid "${POOL_NAME}/c@s0")

# Bookmark guid should equal guid of all snapshots
if [ "${bookmark_guid}" != "${snap_a_guid}" ] || \
   [ "${bookmark_guid}" != "${snap_b_guid}" ] || \
   [ "${bookmark_guid}" != "${snap_c_guid}" ]; then
  exit 1
fi

bookmark_suffix="${bookmark_guid:0:6}"
fallback_bookmark="${POOL_NAME}/a#s0${bookmark_suffix}"

# Fallback bookmark should not exist
if zfs get guid "${fallback_bookmark}"; then
  exit 1
fi

zfs snapshot "${POOL_NAME}/a@s1"

# Create bookmark so syncoid is forced to create fallback bookmark
zfs bookmark "${POOL_NAME}/a@s0" "${POOL_NAME}/a#s1"

# This incrementally replicates from a@s0 to a@s1 and should create a
# bookmark with fallback suffix
../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b

snap_guid=$(getGuid "${POOL_NAME}/a@s1")
bookmark_suffix="${snap_guid:0:6}"
fallback_bookmark="${POOL_NAME}/a#s1${bookmark_suffix}"

# Fallback bookmark guid should equal guid of snapshot
if [ "$(getGuid "${fallback_bookmark}")" != "${snap_guid}" ]; then
  exit 1
fi

zfs snapshot "${POOL_NAME}/a@s2"

snap_guid=$(getGuid "${POOL_NAME}/a@s2")
bookmark_suffix="${snap_guid:0:6}"
fallback_bookmark="${POOL_NAME}/a#s2${bookmark_suffix}"

# Create bookmark and fallback bookmark so syncoid should fail
zfs bookmark "${POOL_NAME}/a@s0" "${POOL_NAME}/a#s2"
zfs bookmark "${POOL_NAME}/a@s0" "${fallback_bookmark}"

# This incrementally replicates from a@s1 to a@s2 and should fail to create a
# bookmark with fallback suffix
if ../../../syncoid --debug --no-sync-snap --no-rollback --create-bookmark "${POOL_NAME}"/a "${POOL_NAME}"/b; then
  exit 1
fi

exit 0
