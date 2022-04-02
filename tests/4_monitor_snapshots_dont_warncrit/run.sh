#!/bin/bash
set -x

# this test will create pools in a number of states
# and check the output text and return code of 
# sanoid --monitor-snapshots

. ../common/lib.sh

# prepare
setup
checkEnvironment
disableTimeSync

# set timezone
ln -sf /usr/share/zoneinfo/Europe/Vienna /etc/localtime

python3 test_monitoring.py
