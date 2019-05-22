#!/bin/bash

# test no resume replication with a target containing a partially received replication stream

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-5.zpool"
MOUNT_TARGET="/tmp/syncoid-test-5.mount"
POOL_SIZE="1000M"
POOL_NAME="syncoid-test-5"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src -o mountpoint="${MOUNT_TARGET}"
../../../syncoid --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

dd if=/dev/urandom of="${MOUNT_TARGET}"/big_file bs=1M count=200

../../../syncoid --debug --compress=none --source-bwlimit=2m "${POOL_NAME}"/src "${POOL_NAME}"/dst &
syncoid_pid=$!
sleep 5
list_descendants ()
{
  local children=$(ps -o pid= --ppid "$1")

  for pid in $children
  do
    list_descendants "$pid"
  done

  echo "$children"
}

kill $(list_descendants $$) || true
wait
sleep 1

../../../syncoid --debug --compress=none --no-resume "${POOL_NAME}"/src "${POOL_NAME}"/dst | grep "reset partial receive state of syncoid"
../../../syncoid --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

exit $?
