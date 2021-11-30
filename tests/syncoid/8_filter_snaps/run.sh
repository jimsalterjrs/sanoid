#!/bin/bash

# test filtering snapshot names using --include-snaps and --exclude-snaps

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-8.zpool"
MOUNT_TARGET="/tmp/syncoid-test-8.mount"
POOL_SIZE="100M"
POOL_NAME="syncoid-test-8"

truncate -s "${POOL_SIZE}" "${POOL_IMAGE}"

zpool create -m none -f "${POOL_NAME}" "${POOL_IMAGE}"

#####
# Create source snapshots and destroy the destination snaps and dataset.
#####
function setup_snaps {
  # create intermediate snapshots
  # sleep is needed so creation time can be used for proper sorting
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@monthly1
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@daily1
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@daily2
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@hourly1
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@hourly2
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@daily3
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@hourly3
  sleep 1
  zfs snapshot "${POOL_NAME}"/src@hourly4
}

#####
# Remove the destination snapshots and dataset so that each test starts with a
# blank slate.
#####
function clean_snaps {
  zfs destroy "${POOL_NAME}"/dst@%
  zfs destroy "${POOL_NAME}"/dst
}

#####
# Verify that the correct set of snapshots is present on the destination.
#####
function verify_checksum {
  zfs list -r -t snap "${POOL_NAME}"

  checksum=$(zfs list -t snap -r -H -o name "${POOL_NAME}" | sed 's/@syncoid_.*/@syncoid_/' | shasum -a 256)

  echo "Expected checksum: $1"
  echo "Actual checksum: $checksum"
  return $( [[ "$checksum" == "$1" ]] )
}

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

zfs create "${POOL_NAME}"/src
setup_snaps

#####
# TEST 1
#
# --exclude-snaps is provided and --no-stream is omitted.  Hourly snaps should
# be missing from the destination, and all other intermediate snaps should be
# present.
#####

../../../syncoid --debug --compress=none --no-sync-snap --exclude-snaps='hourly' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum 'fb408c21b8540b3c1bd04781b6091d77ff9432defef3303c1a34321b45e8b6a9  -'
clean_snaps

#####
# TEST 2
#
# --exclude-snaps and --no-stream are provided.  Only the daily3 snap should be
# present on the destination.
#####

../../../syncoid --debug --compress=none --no-sync-snap --exclude-snaps='hourly' --no-stream "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum 'c9ad1d3e07156847f957509fcd4805edc7d4c91fe955c605ac4335076367d19a  -'
clean_snaps

#####
# TEST 3
#
# --include-snaps is provided and --no-stream is omitted.  Hourly snaps should
# be present on the destination, and all other snaps should be missing
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum 'f2fb62a2b475bec85796dbf4f6c02af5b4ccaca01f9995ef3d0909787213cbde  -'
clean_snaps

#####
# TEST 4
#
# --include-snaps and --no-stream are provided.  Only the hourly4 snap should
# be present on the destination.
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' --no-stream "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '194e60e9d635783f7c7d64e2b0d9f0897c926e69a86ffa2858cf0ca874ffeeb4  -'
clean_snaps

#####
# TEST 5
#
# --include-snaps='hourly' and --exclude-snaps='3' are both provided. The
# hourly snaps should be present on the destination except for hourly3; daily
# and monthly snaps should be missing.
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' --exclude-snaps='3' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '55267405e346e64d6f7eed29d62bc9bb9ea0e15c9515103a92ee47a7439a99a2  -'
clean_snaps

#####
# TEST 6
#
# --exclude-snaps='syncoid' and --no-stream are provided, and --no-sync-snap is
# omitted. The sync snap should be created on the source but not sent to the
# destination; only hourly4 should be sent.
#####

../../../syncoid --debug --compress=none --no-stream --exclude-snaps='syncoid' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '47380e1711d08c46fb1691fa4bd65e5551084fd5b961baa2de7f91feff2cb4b8  -'
clean_snaps
