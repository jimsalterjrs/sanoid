#!/bin/bash

# test verifying syncoid behavior with partial transfers

set -x

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-012.zpool"
POOL_SIZE="128M"
POOL_NAME="syncoid-test-012"
MOUNT_TARGET="/tmp/syncoid-test-012.mount"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -O mountpoint="${MOUNT_TARGET}" -f "${POOL_NAME}" "${POOL_IMAGE}"

function cleanUp {
  zpool destroy "${POOL_NAME}"
  rm -f "${POOL_IMAGE}"
}

# Clean up the pool and image file on exit
trap cleanUp EXIT

zfs create "${POOL_NAME}/source"
zfs snap "${POOL_NAME}/source@empty"
dd if=/dev/urandom of="${MOUNT_TARGET}/source/garbage.bin" bs=1M count=16
zfs snap "${POOL_NAME}/source@something"

# Simulate interrupted transfer
zfs send -pwR "${POOL_NAME}/source@something" | head --bytes=8M | zfs recv -s "${POOL_NAME}/destination"

# Using syncoid to continue interrupted transfer
../../../syncoid --sendoptions="pw" "${POOL_NAME}/source" "${POOL_NAME}/destination"

# Check if syncoid succeeded in handling the interrupted transfer
if [ $? -eq 0 ]; then
  echo "Syncoid resumed transfer successfully."

  # Verify data integrity with sha256sum comparison
  original_sum=$(sha256sum "${MOUNT_TARGET}/source/garbage.bin" | cut -d ' ' -f 1)
  received_sum=$(sha256sum "${MOUNT_TARGET}/destination/garbage.bin" | cut -d ' ' -f 1)

  if [ "${original_sum}" == "${received_sum}" ]; then
    echo "Data integrity verified."
    exit 0
  else
    echo "Data integrity check failed."
    exit 1
  fi
else
  echo "Regression detected: syncoid did not handle the resuming correctly."
  exit 1
fi
