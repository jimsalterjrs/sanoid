#!/bin/bash
set -x

# this test will check the behaviour arround a date where DST ends
# with hourly, daily and monthly snapshots checked in a 15 minute interval

# Daylight saving time 2017 in Europe/Vienna began at 02:00 on Sunday, 26 March
# and ended at 03:00 on Sunday, 29 October. All times are in
# Central European Time.

. ../common/lib.sh

POOL_NAME="sanoid-test-2"
POOL_TARGET=""  # root
RESULT="/tmp/sanoid_test_result"
RESULT_CHECKSUM="a916d9cd46f4b80f285d069f3497d02671bbb1bfd12b43ef93531cbdaf89d55c"

# UTC timestamp of start and end
START="1509141600"
END="1509400800"

# prepare
setup
checkEnvironment
disableTimeSync

# set timezone
ln -sf /usr/share/zoneinfo/Europe/Vienna /etc/localtime

timestamp=$START

mkdir -p "${POOL_TARGET}"
truncate -s 512M "${POOL_TARGET}"/zpool2.img

zpool create -f "${POOL_NAME}" "${POOL_TARGET}"/zpool2.img

function cleanUp {
  zpool export "${POOL_NAME}"
}

# export pool in any case
trap cleanUp EXIT

while [ $timestamp -le $END ]; do
    date --utc --set @$timestamp; date; "${SANOID}" --cron --verbose
    timestamp=$((timestamp+900))
done

saveSnapshotList "${POOL_NAME}" "${RESULT}"

# hourly daily monthly
verifySnapshotList "${RESULT}" 73 3 1 "${RESULT_CHECKSUM}"

# one more hour because of DST
