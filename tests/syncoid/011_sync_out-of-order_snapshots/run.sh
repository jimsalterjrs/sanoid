#!/bin/bash

# test verifying snapshots with out-of-order snapshot creation datetimes

set -x
set -e

. ../../common/lib.sh

if [ -z "$ALLOW_INVASIVE_TESTS" ]; then
  exit 130
fi
exit 0
POOL_IMAGE="/tmp/syncoid-test-11.zpool"
POOL_SIZE="64M"
POOL_NAME="syncoid-test-11"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool export "${POOL_NAME}"
  rm -f "${POOL_IMAGE}"
}

# export pool and remove the image in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/before
zfs snapshot "${POOL_NAME}"/before@this-snapshot-should-make-it-into-the-after-dataset

disableTimeSync
setdate 1155533696
zfs snapshot "${POOL_NAME}"/before@oldest-snapshot

zfs snapshot "${POOL_NAME}"/before@another-snapshot-does-not-matter
../../../syncoid --sendoptions="Lec" "${POOL_NAME}"/before "${POOL_NAME}"/after

# verify
saveSnapshotList "${POOL_NAME}" "snapshot-list.txt"

grep "${POOL_NAME}/before@this-snapshot-should-make-it-into-the-after-dataset" "snapshot-list.txt" || exit $?
grep "${POOL_NAME}/after@this-snapshot-should-make-it-into-the-after-dataset" "snapshot-list.txt" || exit $?
grep "${POOL_NAME}/before@oldest-snapshot" "snapshot-list.txt" || exit $?
grep "${POOL_NAME}/after@oldest-snapshot" "snapshot-list.txt" || exit $?
grep "${POOL_NAME}/before@another-snapshot-does-not-matter" "snapshot-list.txt" || exit $?
grep "${POOL_NAME}/after@another-snapshot-does-not-matter" "snapshot-list.txt" || exit $?

exit 0
