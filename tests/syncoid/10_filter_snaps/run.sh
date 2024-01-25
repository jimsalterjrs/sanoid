#!/bin/bash

# test filtering snapshot names using --include-snaps and --exclude-snaps

set -x
set -e

. ../../common/lib.sh

POOL_IMAGE="/tmp/syncoid-test-10.zpool"
MOUNT_TARGET="/tmp/syncoid-test-10.mount"
POOL_SIZE="100M"
POOL_NAME="syncoid-test-10"

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
verify_checksum '494b6860415607f1d670e4106a10e1316924ba6cd31b4ddacffe0ad6d30a6339  -'
clean_snaps

#####
# TEST 2
#
# --exclude-snaps and --no-stream are provided.  Only the daily3 snap should be
# present on the destination.
#####

../../../syncoid --debug --compress=none --no-sync-snap --exclude-snaps='hourly' --no-stream "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '0a5072f42180d231cfdd678682972fbbb689140b7f3e996b3c348b7e78d67ea2  -'
clean_snaps

#####
# TEST 3
#
# --include-snaps is provided and --no-stream is omitted.  Hourly snaps should
# be present on the destination, and all other snaps should be missing
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum 'd32862be4c71c6cde846322a7d006fd5e8edbd3520d3c7b73953492946debb7f  -'
clean_snaps

#####
# TEST 4
#
# --include-snaps and --no-stream are provided.  Only the hourly4 snap should
# be present on the destination.
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' --no-stream "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '81ef1a8298006a7ed856430bb7e05e8b85bbff530ca9dd7831f1da782f8aa4c7  -'
clean_snaps

#####
# TEST 5
#
# --include-snaps='hourly' and --exclude-snaps='3' are both provided. The
# hourly snaps should be present on the destination except for hourly3; daily
# and monthly snaps should be missing.
#####

../../../syncoid --debug --compress=none --no-sync-snap --include-snaps='hourly' --exclude-snaps='3' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '5a9dd92b7d4b8760a1fcad03be843da4f43b915c64caffc1700c0d59a1581239  -'
clean_snaps

#####
# TEST 6
#
# --exclude-snaps='syncoid' and --no-stream are provided, and --no-sync-snap is
# omitted. The sync snap should be created on the source but not sent to the
# destination; only hourly4 should be sent.
#####

../../../syncoid --debug --compress=none --no-stream --exclude-snaps='syncoid' "${POOL_NAME}"/src "${POOL_NAME}"/dst
verify_checksum '9394fdac44ec72764a4673202552599684c83530a2a724dae5b411aaea082b02  -'
clean_snaps
