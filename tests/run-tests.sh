#!/bin/bash

# run's all the available tests

for test in $(find . -mindepth 1 -maxdepth 1 -type d -printf "%P\n" | sort -g); do
    if [ ! -x "${test}/run.sh" ]; then
        continue
    fi

    testName="${test%/}"

    LOGFILE=/tmp/sanoid_test_run_"${testName}".log

    pushd . > /dev/null

    echo -n "Running test ${testName} ... "
    cd "${test}"
    echo -n y | bash run.sh > "${LOGFILE}" 2>&1

    if [ $? -eq 0 ]; then
        echo "[PASS]"
    else
        echo "[FAILED] (see ${LOGFILE})"
    fi

    popd > /dev/null
done
