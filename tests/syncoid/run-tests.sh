#!/bin/bash

# run's all the available tests

for test in $(find . -mindepth 1 -maxdepth 1 -type d -printf "%P\n" | sort -g); do
    if [ ! -x "${test}/run.sh" ]; then
        continue
    fi

    testName="${test%/}"

    LOGFILE=/tmp/syncoid_test_run_"${testName}".log

    pushd . > /dev/null

    echo -n "Running test ${testName} ... "
    cd "${test}"
    echo | bash run.sh > "${LOGFILE}" 2>&1

    ret=$?
    if [ $ret -eq 0 ]; then
        echo "[PASS]"
    elif [ $ret -eq 130 ]; then
        echo "[SKIPPED]"
    else
        echo "[FAILED] (see ${LOGFILE})"
    fi

    popd > /dev/null
done
