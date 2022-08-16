### Requirements ###
Tests must be run inside a virtual machine. This is for your own safety, as the tests may create and destroy zpools etc. 
The tests require a reasonable amount of storage space, so create a VM with 35GB or more of disk. 

You can create a suitable VM with LXD and go straight to a shell to start testing as follows:
```
lxc init ubuntu:focal sanoid-test --vm -c limits.cpu=8 -c limits.memory=4GB
lxc start sanoid-test
lxc exec sanoid-test /bin/bash
```
One of the tests traverses an entire year running Sanoid every hour, which takes a long time. The tests can take over 5 hours to complete.

#### Packages ####
The tests require the following packages to be installed in the VM (Ubuntu 20.04 package names are used, translate as appropriate):
```
zfsutils-linux
libconfig-inifiles-perl
libcapture-tiny-perl
libjson-perl
```
```
apt install zfsutils-linux libconfig-inifiles-perl libcapture-tiny-perl libjson-perl
```

#### Clone the sanoid repo into the VM ####
Clone the sanoid repo (or your fork of it) within the VM, for example:
```
apt install git
git clone https://github.com/jimsalterjrs/sanoid.git
cd sanoid
```
Switch to the branch you are working in, e.g.:
```
git checkout my_feature_branch
```


### Run the tests ##
This requires root/sudo privileges.
```
cd tests/
./run-tests.sh
```
