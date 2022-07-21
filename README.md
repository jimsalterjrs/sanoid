<p align="center"><img src="http://www.openoid.net/wp-content/themes/openoid/images/sanoid_logo.png" alt="sanoid logo" title="sanoid logo"></p>

<img src="http://openoid.net/gplv3-127x51.png" width=127 height=51 align="right">Sanoid is a policy-driven snapshot management tool for ZFS filesystems.  When combined with the Linux KVM hypervisor, you can use it to make your systems <a href="http://openoid.net/transcend" target="_blank">functionally immortal</a>.  

<p align="center"><a href="https://youtu.be/ZgowLNBsu00" target="_blank"><img src="http://www.openoid.net/sanoid_video_launcher.png" alt="sanoid rollback demo" title="sanoid rollback demo"></a><br clear="all"><sup>(Real time demo: rolling back a full-scale cryptomalware infection in seconds!)</sup></p>

More prosaically, you can use Sanoid to create, automatically thin, and monitor snapshots and pool health from a single eminently human-readable TOML config file at /etc/sanoid/sanoid.conf.  (Sanoid also requires a "defaults" file located at /etc/sanoid/sanoid.defaults.conf, which is not user-editable.)  A typical Sanoid system would have a single cron job but see INSTALL.md fore more details:
```
* * * * * TZ=UTC /usr/local/bin/sanoid --cron
```

`Note`: Using UTC as timezone is recommend to prevent problems with daylight saving times

And its /etc/sanoid/sanoid.conf might look something like this:

```
[data/home]
	use_template = production
[data/images]
	use_template = production
	recursive = yes
	process_children_only = yes
[data/images/win7]
	hourly = 4

#############################
# templates below this line #
#############################

[template_production]
        frequently = 0
        hourly = 36
        daily = 30
        monthly = 3
        yearly = 0
        autosnap = yes
        autoprune = yes
```

Which would be enough to tell sanoid to take and keep 36 hourly snapshots, 30 dailies, 3 monthlies, and no yearlies for all datasets under data/images (but not data/images itself, since process_children_only is set).  Except in the case of data/images/win7, which follows the same template (since it's a child of data/images) but only keeps 4 hourlies for whatever reason.

For more full details on sanoid.conf settings see [Wiki page](https://github.com/jimsalterjrs/sanoid/wiki/Sanoid#options).

**Note**: Be aware that if you don't specify some interval options the defaults will be used (from /etc/sanoid/sanoid.defaults.conf)

##### Sanoid Command Line Options

+ --cron

 	This will process your sanoid.conf file, create snapshots, then purge expired ones.

+ --configdir

	Specify a location for the config file named sanoid.conf. Defaults to /etc/sanoid

+ --cache-dir

	Specify a directory to store the zfs snapshot cache. Defaults to /var/cache/sanoid

+ --run-dir

	Specify a directory for temporary files such as lock files. Defaults to /var/run/sanoid

+ --take-snapshots

	This will process your sanoid.conf file, create snapshots, but it will NOT purge expired ones. (Note that snapshots taken are atomic in an individual dataset context, <i>not</i> a global context - snapshots of pool/dataset1 and pool/dataset2 will each be internally consistent and atomic, but one may be a few filesystem transactions "newer" than the other.)

+ --prune-snapshots

	This will process your sanoid.conf file, it will NOT create snapshots, but it will purge expired ones.

+ --force-prune

	Purges expired snapshots even if a send/recv is in progress

+ --monitor-snapshots

	This option is designed to be run by a Nagios monitoring system. It reports on the health of your snapshots.

+ --monitor-health

	This option is designed to be run by a Nagios monitoring system. It reports on the health of the zpool your filesystems are on. It only monitors filesystems that are configured in the sanoid.conf file.

+ --monitor-capacity

	This option is designed to be run by a Nagios monitoring system. It reports on the capacity of the zpool your filesystems are on. It only monitors pools that are configured in the sanoid.conf file.

+ --force-update

	This clears out sanoid's zfs snapshot listing cache. This is normally not needed.

+ --version

	This prints the version number, and exits.

+ --quiet

	Supress non-error output.

+ --verbose

	This prints additional information during the sanoid run.

+ --debug

	This prints out quite alot of additional information during a sanoid run, and is normally not needed.

+ --readonly

	Skip creation/deletion of snapshots (Simulate).

+ --help

	Show help message.

### Sanoid script hooks

There are three script types which can optionally be executed at various stages in the lifecycle of a snapshot:

#### `pre_snapshot_script`

Will be executed before the snapshot(s) of a single dataset are taken. The following environment variables are passed:

| Env vars           | Description                                                                                                                                          |
| -----------------  | -----------                                                                                                                                          |
| `SANOID_SCRIPT`    | The type of script being executed, one of `pre`, `post`, or `prune`.  Allows for one script to be used for multiple tasks                            |
| `SANOID_TARGET`    | **DEPRECATED** The dataset about to be snapshot (only the first dataset will be provided)                                                            |
| `SANOID_TARGETS`   | Comma separated list of all datasets to be snapshoted (currently only a single dataset, multiple datasets will be possible later with atomic groups) |
| `SANOID_SNAPNAME`  | **DEPRECATED** The name of the snapshot that will be taken (only the first name will be provided, does not include the dataset name)                 |
| `SANOID_SNAPNAMES` | Comma separated list of all snapshot names that will be taken (does not include the dataset name)                                                    |
| `SANOID_TYPES`     | Comma separated list of all snapshot types to be taken (yearly, monthly, weekly, daily, hourly, frequently)                                          |

If the script returns a non-zero exit code, the snapshot(s) will not be taken unless `no_inconsistent_snapshot` is false.

#### `post_snapshot_script`

Will be executed when:

- The pre-snapshot script succeeded or
- The pre-snapshot script failed and `force_post_snapshot_script` is true.

| Env vars             | Description                                          |
| -------------------- | -----------                                          |
| `SANOID_SCRIPT`      | as above                                             |
| `SANOID_TARGET`      | **DEPRECATED** as above                              |
| `SANOID_TARGETS`     | as above                                             |
| `SANOID_SNAPNAME`    | **DEPRECATED** as above                              |
| `SANOID_SNAPNAMES`   | as above                                             |
| `SANOID_TYPES`       | as above                                             |
| `SANOID_PRE_FAILURE` | This will indicate if the pre-snapshot script failed |

#### `pruning_script`

Will be executed after a snapshot is successfully deleted. The following environment variables will be passed:

| Env vars          | Description |
| ----------------- | ----------- |
| `SANOID_SCRIPT`   | as above    |
| `SANOID_TARGET`   | as above    |
| `SANOID_SNAPNAME` | as above    |


#### example

**sanoid.conf**:
```
...
[sanoid-test-0]
	use_template = production
	recursive = yes
	pre_snapshot_script = /tmp/debug.sh
	post_snapshot_script = /tmp/debug.sh
	pruning_script = /tmp/debug.sh
...
```

**verbose sanoid output**:
```
...
executing pre_snapshot_script '/tmp/debug.sh' on dataset 'sanoid-test-0'
taking snapshot sanoid-test-0@autosnap_2020-02-12_14:49:33_yearly
taking snapshot sanoid-test-0@autosnap_2020-02-12_14:49:33_monthly
taking snapshot sanoid-test-0@autosnap_2020-02-12_14:49:33_daily
taking snapshot sanoid-test-0@autosnap_2020-02-12_14:49:33_hourly
executing post_snapshot_script '/tmp/debug.sh' on dataset 'sanoid-test-0'
...
```

**pre script env variables**:
```
SANOID_SCRIPT=pre
SANOID_TARGET=sanoid-test-0/b/bb
SANOID_TARGETS=sanoid-test-0/b/bb
SANOID_SNAPNAME=autosnap_2020-02-12_14:49:32_yearly
SANOID_SNAPNAMES=autosnap_2020-02-12_14:49:32_yearly,autosnap_2020-02-12_14:49:32_monthly,autosnap_2020-02-12_14:49:32_daily,autosnap_2020-02-12_14:49:32_hourly
SANOID_TYPES=yearly,monthly,daily,hourly
```

**post script env variables**:
```
SANOID_SCRIPT=post
SANOID_TARGET=sanoid-test-0/b/bb
SANOID_TARGETS=sanoid-test-0/b/bb
SANOID_SNAPNAME=autosnap_2020-02-12_14:49:32_yearly
SANOID_SNAPNAMES=autosnap_2020-02-12_14:49:32_yearly,autosnap_2020-02-12_14:49:32_monthly,autosnap_2020-02-12_14:49:32_daily,autosnap_2020-02-12_14:49:32_hourly
SANOID_TYPES=yearly,monthly,daily,hourly
SANOID_PRE_FAILURE=0
```

----------

# Syncoid

Sanoid also includes a replication tool, syncoid, which facilitates the asynchronous incremental replication of ZFS filesystems.  A typical syncoid command might look like this:

```
syncoid data/images/vm backup/images/vm
```

Which would replicate the specified ZFS filesystem (aka dataset) from the data pool to the backup pool on the local system, or

```
syncoid data/images/vm root@remotehost:backup/images/vm
```

Which would push-replicate the specified ZFS filesystem from the local host to remotehost over an SSH tunnel, or

```
syncoid root@remotehost:data/images/vm backup/images/vm
```

Which would pull-replicate the filesystem from the remote host to the local system over an SSH tunnel.

Syncoid supports recursive replication (replication of a dataset and all its child datasets) and uses mbuffer buffering, lzop compression, and pv progress bars if the utilities are available on the systems used.
If ZFS supports resumeable send/receive streams on both the source and target those will be enabled as default.

As of 1.4.18, syncoid also automatically supports and enables resume of interrupted replication when both source and target support this feature.

##### Syncoid Dataset Properties

+ syncoid:sync

  Available values:

  + `true` (default if unset)

    This dataset will be synchronised to all hosts.

  + `false`

    This dataset will not be synchronised to any hosts - it will be skipped. This can be useful for preventing certain datasets from being transferred when recursively handling a tree.

  + `host1,host2,...`

    A comma separated list of hosts. This dataset will only be synchronised by hosts listed in the property.

    _Note_: this check is performed by the host running `syncoid`, thus the local hostname must be present for inclusion during a push operation // the remote hostname must be present for a pull.

  _Note_: this will also prevent syncoid from handling the dataset if given explicitly on the command line.

  _Note_: syncing a child of a no-sync dataset will currently result in a critical error.

  _Note_: empty properties will be handled as if they were unset.

##### Syncoid Command Line Options

+ [source]

	This is the source dataset. It can be either local or remote.

+ [destination]

	This is the destination dataset. It can be either local or remote.

+ --identifier=

	Adds the given identifier to the snapshot name after "syncoid_" prefix and before the hostname. This enables the use case of reliable replication to multiple targets from the same host. The following chars are allowed: a-z, A-Z, 0-9, _, -, : and . .

+ -r --recursive

	This will also transfer child datasets.

+ --skip-parent

	This will skip the syncing of the parent dataset. Does nothing without '--recursive' option.

+ --compress <compression type>

	Currently accepted options: gzip, pigz-fast, pigz-slow, zstd-fast, zstd-slow, lz4, xz, lzo (default) & none. If the selected compression method is unavailable on the source and destination, no compression will be used.

+ --source-bwlimit <limit t|g|m|k>

	This is the bandwidth limit in bytes (kbytes, mbytes, etc) per second imposed upon the source. This is mainly used if the target does not have mbuffer installed, but bandwidth limits are desired.

+ --target-bwlimit <limit t|g|m|k>

	This is the bandwidth limit in bytes (kbytes, mbytesm etc) per second imposed upon the target. This is mainly used if the source does not have mbuffer installed, but bandwidth limits are desired.

+ --no-command-checks

	Does not check the existence of commands before attempting the transfer, providing administrators a way to run the tool with minimal overhead and maximum speed, at risk of potentially failed replication, or other possible edge cases. It assumes all programs are available, and should not be used in most situations. This is an not an officially supported run mode.

+ --no-stream

	This argument tells syncoid to use -i incrementals, not -I. This updates the target with the newest snapshot from the source, without replicating the intermediate snapshots in between. (If used for an initial synchronization, will do a full replication from newest snapshot and exit immediately, rather than starting with the oldest and then doing an immediate -i to the newest.)

+ --no-sync-snap

	This argument tells syncoid to restrict itself to existing snapshots, instead of creating a semi-ephemeral syncoid snapshot at execution time. Especially useful in multi-target (A->B, A->C) replication schemes, where you might otherwise accumulate a large number of foreign syncoid snapshots.

+ --keep-sync-snap

    This argument tells syncoid to skip pruning old snapshots created and used by syncoid for replication if '--no-sync-snap' isn't specified.

+ --create-bookmark

	This argument tells syncoid to create a zfs bookmark for the newest snapshot after it got replicated successfully. The bookmark name will be equal to the snapshot name. Only works in combination with the --no-sync-snap option. This can be very useful for irregular replication where the last matching snapshot on the source was already deleted but the bookmark remains so a replication is still possible.

+ --preserve-recordsize

	This argument tells syncoid to set the recordsize on the target before writing any data to it matching the one set on the replication src. This only applies to initial sends.

+ --no-forced-receive

	This argument tells syncoid to not force a receive (-F flag) on the target dataset. This will prevent snapshots that do not exist on the source from being destroyed on the target before performing the receive operation.

+ --exclude=REGEX

	The given regular expression will be matched against all datasets which would be synced by this run and excludes them. This argument can be specified multiple times.

+ --no-resume

	This argument tells syncoid to not use resumeable zfs send/receive streams.

+ --force-delete

	Remove target datasets recursively (WARNING: this will also affect child datasets with matching snapshots/bookmarks), if there are no matching snapshots/bookmarks.

+ --no-clone-handling

	This argument tells syncoid to not recreate clones on the targe on initial sync and doing a normal replication instead.

+ --dumpsnaps

	This prints a list of snapshots during the run.

+ --no-privilege-elevation

	Bypass the root check and assume syncoid has the necessary permissions (for use with ZFS permission delegation).

+ --sshport

	Allow sync to/from boxes running SSH on non-standard ports.

+ --sshcipher

	Instruct ssh to use a particular cipher set.

+ --sshoption

	Passes option to ssh. This argument can be specified multiple times.

+ --sshkey

	Use specified identity file as per ssh -i.

+ --quiet

	Supress non-error output.

+ --debug

	This prints out quite alot of additional information during a sanoid run, and is normally not needed.

+ --help

	Show help message.

+ --version

	Print the version and exit.

+ --monitor-version

	This doesn't do anything right now.

Note that the sync snapshots syncoid creates are not atomic in a global context: sync snapshots of pool/dataset1 and pool/dataset2 will each be internally consistent, but one may be a few filesystem transactions "newer" than the other.  (This does not affect the consistency of snapshots already taken in other ways, which syncoid replicates in the overall stream unless --no-stream is specified. So if you want to manually zfs snapshot -R pool@1 before replicating with syncoid, the global atomicity of pool/dataset1@1 and pool/dataset2@1 will still be intact.)
