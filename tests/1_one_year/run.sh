#!/bin/bash
set -x

# this test will take hourly, daily and monthly snapshots
# for the whole year of 2017 in the timezone Europe/Vienna
# sanoid is run hourly and no snapshots are pruned

. ../common/lib.sh

POOL_NAME="sanoid-test-1"
POOL_TARGET=""  # root
RESULT="/tmp/sanoid_test_result"
RESULT_CHECKSUM="aa15e5595b0ed959313289ecb70323dad9903328ac46e881da5c4b0f871dd7cf"

# UTC timestamp of start and end
START="1483225200"
END="1514761199"

# prepare
setup
checkEnvironment
disableTimeSync

# set timezone
ln -sf /usr/share/zoneinfo/Europe/Vienna /etc/localtime

timestamp=$START

mkdir -p "${POOL_TARGET}"
truncate -s 5120M "${POOL_TARGET}"/zpool.img

zpool create -f "${POOL_NAME}" "${POOL_TARGET}"/zpool.img

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

while [ $timestamp -le $END ]; do
    date --utc --set @$timestamp; date; "${SANOID}" --cron --verbose
    timestamp=$((timestamp+3600))
done

saveSnapshotList "${POOL_NAME}" "${RESULT}"

# hourly daily monthly
verifySnapshotList "${RESULT}" 8759 366 12 "${RESULT_CHECKSUM}"

# hourly count should be 8760 but one hour get's lost because of DST

# daily count should be 365 but one additional daily is taken
# because the DST change leads to a day with 25 hours
# which will trigger an additional daily snapshot
