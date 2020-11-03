# Installation

**Sanoid** and **Syncoid** are complementary but separate pieces of software. To install and configure them, follow the guide below for your operating system. Everything in `code blocks` should be copy-pasteable. If your OS isn't listed, a set of general instructions is at the end of the list and you can perform the process manually.

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:0 orderedList:0 -->

- [Installation](#installation)
	- [Debian/Ubuntu](#debianubuntu)
	- [CentOS](#centos)
	- [FreeBSD](#freebsd)
	- [Alpine Linux / busybox](#alpine-Linux-busybox-based-distributions)
	- [Other OSes](#other-oses)
- [Configuration](#configuration)
	- [Sanoid](#sanoid)

<!-- /TOC -->


## Debian/Ubuntu

Install prerequisite software:

```bash

apt install debhelper libcapture-tiny-perl libconfig-inifiles-perl pv lzop mbuffer build-essential

```

Clone this repo, build the debian package and install it (alternatively you can skip the package and do it manually like described below for CentOS):

```bash
# Download the repo as root to avoid changing permissions later
sudo git clone https://github.com/jimsalterjrs/sanoid.git
cd sanoid
# checkout latest stable release or stay on master for bleeding edge stuff (but expect bugs!)
git checkout $(git tag | grep "^v" | tail -n 1)
ln -s packages/debian .
dpkg-buildpackage -uc -us
apt install ../sanoid_*_all.deb
```

Enable sanoid timer:
```bash
# enable and start the sanoid timer
sudo systemctl enable sanoid.timer
sudo systemctl start sanoid.timer
```

## CentOS

Install prerequisite software:

```bash
# Install and enable epel if we don't already have it, and git too
sudo yum install -y epel-release git
# Install the packages that Sanoid depends on:
sudo yum install -y perl-Config-IniFiles perl-Data-Dumper perl-Capture-Tiny lzop mbuffer mhash pv
# if the perl dependencies can't be found in the configured repositories you can install them from CPAN manually:
sudo dnf install perl-CPAN perl-CPAN
cpan # answer the questions and past the following lines
# install Capture::Tiny
# install Config::IniFiles
```

Clone this repo, then put the executables and config files into the appropriate directories:

```bash
# Download the repo as root to avoid changing permissions later
sudo git clone https://github.com/jimsalterjrs/sanoid.git
cd sanoid
# checkout latest stable release or stay on master for bleeding edge stuff (but expect bugs!)
git checkout $(git tag | grep "^v" | tail -n 1)
# Install the executables
sudo cp sanoid syncoid findoid sleepymutex /usr/local/sbin
# Create the config directory
sudo mkdir /etc/sanoid
# Install default config
sudo cp sanoid.defaults.conf /etc/sanoid
# Create a blank config file
sudo touch /etc/sanoid/sanoid.conf
# Place the sample config in the conf directory for reference
sudo cp sanoid.conf /etc/sanoid/sanoid.example.conf
```

Create a systemd service:

```bash
cat << "EOF" | sudo tee /etc/systemd/system/sanoid.service
[Unit]
Description=Snapshot ZFS Pool
Requires=zfs.target
After=zfs.target
Wants=sanoid-prune.service
Before=sanoid-prune.service
ConditionFileNotEmpty=/etc/sanoid/sanoid.conf

[Service]
Environment=TZ=UTC
Type=oneshot
ExecStart=/usr/local/sbin/sanoid --take-snapshots --verbose
EOF

cat << "EOF" | sudo tee /etc/systemd/system/sanoid-prune.service
[Unit]
Description=Cleanup ZFS Pool
Requires=zfs.target
After=zfs.target sanoid.service
ConditionFileNotEmpty=/etc/sanoid/sanoid.conf

[Service]
Environment=TZ=UTC
Type=oneshot
ExecStart=/usr/local/sbin/sanoid --prune-snapshots --verbose

[Install]
WantedBy=sanoid.service
EOF
```

And a systemd timer that will execute **Sanoid** once per quarter hour
(Decrease the interval as suitable for configuration):

```bash
cat << "EOF" | sudo tee /etc/systemd/system/sanoid.timer
[Unit]
Description=Run Sanoid Every 15 Minutes
Requires=sanoid.service

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

Reload systemd and start our timer:
```bash
# Tell systemd about our new service definitions
sudo systemctl daemon-reload
# Enable sanoid-prune.service to allow it to be triggered by sanoid.service
sudo systemctl enable sanoid-prune.service
# Enable and start the Sanoid timer
sudo systemctl enable sanoid.timer
sudo systemctl start sanoid.timer
```

Now, proceed to configure [**Sanoid**](#configuration)

## FreeBSD

Install prerequisite software:

```bash
pkg install p5-Config-Inifiles p5-Capture-Tiny pv mbuffer lzop
```

**Additional notes:**

*   FreeBSD may place pv and lzop in somewhere other than /usr/bin — syncoid currently does not check path.

*   Simplest path workaround is symlinks, eg `ln -s /usr/local/bin/lzop /usr/bin/lzop` or similar, as appropriate to create links in **/usr/bin** to wherever the utilities actually are on your system.

*   See note about mbuffer and other things in FREEBSD.readme

## Alpine Linux / busybox based distributions

The busybox implementation of ps is lacking needed arguments so a proper ps program needs to be installed.
For Alpine Linux this can be done with:

`apk --no-cache add procps`

## Other OSes

**Sanoid** depends on the Perl module Config::IniFiles and will not operate without it. Config::IniFiles may be installed from CPAN, though the project strongly recommends using your distribution's repositories instead.

**Syncoid** depends on ssh, pv, gzip, lzop, and mbuffer. It can run with reduced functionality in the absence of any or all of the above. SSH is only required for remote synchronization. On newer FreeBSD and Ubuntu Xenial chacha20-poly1305@openssh.com, on other distributions arcfour crypto is the default for SSH transport since v1.4.6. Syncoid runs will fail if one of them is not available on either end of the transport.

### General outline for installation

1.  Install prerequisites: Perl module Config::IniFiles, ssh, pv, gzip, lzop, and mbuffer
2.  Download the **Sanoid** repo
3.  Create the config directory `/etc/sanoid` and put `sanoid.defaults.conf` in there, and create `sanoid.conf` in it too
4.  Create a cron job or a systemd timer that runs `sanoid --cron` once per minute

## cron

If you use cron there is the need to ensure that only one instance of sanoid is run at any time (or else there will be funny error messages about missing snapshots, ...). It's also good practice to separate the snapshot taking and pruning so the later won't block the former in case of long running pruning operations. Following is the recommend setup for a standard install:

```
*/15 * * * * root flock -n /var/run/sanoid/cron-take.lock -c "TZ=UTC sanoid --take-snapshots"
*/15 * * * * root flock -n /var/run/sanoid/cron-prune.lock -c "sanoid --prune-snapshots"
```

Adapt the timer interval to the lowest configured snapshot interval.

# Configuration

**Sanoid** won't do anything useful unless you tell it how to handle your ZFS datasets in `/etc/sanoid/sanoid.conf`.

**Syncoid** is a command line utility that doesn't require any configuration, with all of its switches set at runtime.

## Sanoid

Take a look at the files `sanoid.defaults.conf` and `sanoid.conf` for all possible configuration options.

Also have a look at the README.md for a simpler suggestion for `sanoid.conf`.
