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

zfs create -o mountpoint="${MOUNT_TARGET}" "${POOL_NAME}"/src
../../../syncoid --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

dd if=/dev/urandom of="${MOUNT_TARGET}"/big_file bs=1M count=200

../../../syncoid --debug --compress=none --source-bwlimit=2m "${POOL_NAME}"/src "${POOL_NAME}"/dst &
syncoid_pid=$!
sleep 5
function getcpid() {
    cpids=$(pgrep -P "$1"|xargs)
    for cpid in $cpids;
    do
        echo "$cpid"
        getcpid "$cpid"
    done
}

kill $(getcpid $$) || true
wait
sleep 1

../../../syncoid --debug --compress=none --no-resume "${POOL_NAME}"/src "${POOL_NAME}"/dst | grep "reset partial receive state of syncoid"
../../../syncoid --debug --compress=none "${POOL_NAME}"/src "${POOL_NAME}"/dst

exit $?
