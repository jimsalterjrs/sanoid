### Requirements ###
Tests must be run inside a virtual machine. This is for your own safety, as the tests may create and destroy zpools etc.

A VM with 35GB of storage and 8 cores running Ubuntu 20.04 completes the tests in about 5 hours.  

#### Packages ####
The tests require the following packages to be installed in the VM (Ubuntu 20.04 package names are used, translate as appropriate):
```
zfsutils-linux
libconfig-inifiles-perl
libcapture-tiny-perl
```
```
apt install zfsutils-linux libconfig-inifiles-perl libcapture-tiny-perl
```

#### Install sanoid within the VM ####
Install sanoid within the VM, for example
```
apt install git
git clone https://github.com/jimsalterjrs/sanoid.git
mkdir /etc/sanoid/
cp sanoid/sanoid.defaults.conf /etc/sanoid/
```

### Run the tests ##
This requires root/sudo privileges.
```
cd sanoid/tests/
./run-tests.sh
```