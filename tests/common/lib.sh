#!/bin/bash

function setup {
    export LANG=C
    export LANGUAGE=C
    export LC_ALL=C

    export SANOID="../../sanoid"

    # make sure that there is no cache file
    rm -f /var/cache/sanoidsnapshots.txt

    # install needed sanoid configuration files
    [ -f sanoid.conf ] && cp sanoid.conf /etc/sanoid/sanoid.conf
    cp ../../sanoid.defaults.conf /etc/sanoid/sanoid.defaults.conf
}

function checkEnvironment {
    ASK=1

    which systemd-detect-virt > /dev/null
    if [ $? -eq 0 ]; then
        systemd-detect-virt --vm > /dev/null
        if [ $? -eq 0 ]; then
            # we are in a vm
            ASK=0
        fi
    fi

    if [ $ASK -eq 1 ]; then
        set +x
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "you should be running this test in a"
        echo "dedicated vm, as it will mess with your system!"
        echo "Are you sure you wan't to continue? (y)"
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        set -x

        read -n 1 c
        if [ "$c" != "y" ]; then
            exit 1
        fi
    fi
}

function disableTimeSync {
    # disable ntp sync
    which timedatectl > /dev/null
    if [ $? -eq 0 ]; then
        timedatectl set-ntp 0
    fi
}

function saveSnapshotList {
    POOL_NAME="$1"
    RESULT="$2"

    zfs list -t snapshot -o name -Hr "${POOL_NAME}" | sort > "${RESULT}"

    # clear the seconds for comparing
    sed -i 's/\(autosnap_[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]:[0-9][0-9]:\)[0-9][0-9]_/\100_/g' "${RESULT}"
}

function verifySnapshotList {
    RESULT="$1"
    HOURLY_COUNT=$2
    DAILY_COUNT=$3
    MONTHLY_COUNT=$4
    CHECKSUM="$5"

    failed=0
    message=""

    hourly_count=$(grep -c "autosnap_.*_hourly" < "${RESULT}")
    daily_count=$(grep -c "autosnap_.*_daily" < "${RESULT}")
    monthly_count=$(grep -c "autosnap_.*_monthly" < "${RESULT}")

    if [ "${hourly_count}" -ne "${HOURLY_COUNT}" ]; then
        failed=1
        message="${message}hourly snapshot count is wrong: ${hourly_count}\n"
    fi

    if [ "${daily_count}" -ne "${DAILY_COUNT}" ]; then
        failed=1
        message="${message}daily snapshot count is wrong: ${daily_count}\n"
    fi

    if [ "${monthly_count}" -ne "${MONTHLY_COUNT}" ]; then
        failed=1
        message="${message}monthly snapshot count is wrong: ${monthly_count}\n"
    fi

    checksum=$(sha256sum "${RESULT}" | cut -d' ' -f1)
    if [ "${checksum}" != "${CHECKSUM}" ]; then
        failed=1
        message="${message}result checksum mismatch\n"
    fi

    if [ "${failed}" -eq 0 ]; then
        exit 0
    fi

    echo "TEST FAILED:" >&2
    echo -n -e "${message}" >&2

    exit 1
}
