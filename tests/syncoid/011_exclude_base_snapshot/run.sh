#!/bin/bash

# ensure excluded snapshots do not hide the existing base snapshot on the target

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-11.zpool"
POOL_SIZE="100M"
POOL_NAME="syncoid-test-11"
MOUNT_TARGET="/tmp/${POOL_NAME}_mnt"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
	zpool export "${POOL_NAME}"
}

trap cleanUp EXIT

mkdir -p "${MOUNT_TARGET}"
zfs create -o mountpoint="${MOUNT_TARGET}" "${POOL_NAME}"/src

# add data before the first snapshots (ensures receive sees changes)
printf "base\n" >"${MOUNT_TARGET}/file.txt"
dd if=/dev/urandom of="${MOUNT_TARGET}/bump0" bs=1K count=4 status=none

# seed the target with a daily and an excluded hourly base
sleep 1
zfs snapshot "${POOL_NAME}"/src@daily0
sleep 1
dd if=/dev/urandom of="${MOUNT_TARGET}/bump1" bs=1K count=4 status=none
zfs snapshot "${POOL_NAME}"/src@hourly1

# initial replication without filtering (also sets holds for later release)
../../../syncoid --debug --compress=none --no-sync-snap --use-hold "${POOL_NAME}"/src "${POOL_NAME}"/dst

# create new snapshots: an included daily to send and a new excluded hourly to skip
sleep 1
dd if=/dev/urandom of="${MOUNT_TARGET}/bump2" bs=1K count=4 status=none
zfs snapshot "${POOL_NAME}"/src@daily1
sleep 1
dd if=/dev/urandom of="${MOUNT_TARGET}/bump3" bs=1K count=4 status=none
zfs snapshot "${POOL_NAME}"/src@hourly2

# replicate with excludes; should anchor on excluded hourly1, send daily1, skip hourly2
../../../syncoid --debug --compress=none --no-sync-snap --no-rollback --use-hold --exclude-snaps='hourly' "${POOL_NAME}"/src "${POOL_NAME}"/dst

snapshot_list=$(zfs list -t snap -r -H -o name "${POOL_NAME}")
echo "${snapshot_list}"

echo "${snapshot_list}" | grep -q "${POOL_NAME}/dst@daily0"
echo "${snapshot_list}" | grep -q "${POOL_NAME}/dst@hourly1"
echo "${snapshot_list}" | grep -q "${POOL_NAME}/dst@daily1"
! echo "${snapshot_list}" | grep -q "${POOL_NAME}/dst@hourly2"
