<p align="center"><img src="http://www.openoid.net/wp-content/themes/openoid/images/sanoid_logo.png" alt="sanoid logo" title="sanoid logo"></p>
======

<img src="http://openoid.net/gplv3-127x51.png" width=127 height=51 align="right">Sanoid is a policy-driven snapshot management tool for ZFS filesystems.  When combined with the Linux KVM hypervisor, you can use it to make your systems <a href="http://openoid.net/transcend" target="_blank">functionally immortal</a>.  

<p align="center"><a href="https://youtu.be/ZgowLNBsu00" target="_blank"><img src="http://www.openoid.net/sanoid_video_launcher.png" alt="sanoid rollback demo" title="sanoid rollback demo"></a><br clear="all"><sup>(Real time demo: rolling back a full-scale cryptomalware infection in seconds!)</sup></p>

More prosaically, you can use Sanoid to create, automatically thin, and monitor snapshots and pool health from a single eminently human-readable TOML config file at /etc/sanoid/sanoid.conf.  (Sanoid also requires a "defaults" file located at /etc/sanoid/sanoid.defaults.conf, which is not user-editable.)  A typical Sanoid system would have a single cron job:
```
* * * * * /usr/local/bin/sanoid --cron
```

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
        hourly = 36
        daily = 30
        monthly = 3
        yearly = 0
        autosnap = yes
        autoprune = yes
```

Which would be enough to tell sanoid to take and keep 36 hourly snapshots, 30 dailies, 3 monthlies, and no yearlies for all datasets under data/images (but not data/images itself, since process_children_only is set).  Except in the case of data/images/win7-spice, which follows the same template (since it's a child of data/images) but only keeps 4 hourlies for whatever reason.

##### Sanoid Command Line Options

+ --cron

 	This will process your sanoid.conf file, create snapshots, then purge expired ones.

+ --configdir

	Specify a location for the config file named sanoid.conf. Defaults to /etc/sanoid

+ --take-snapshots

	This will process your sanoid.conf file, create snapshots, but it will NOT purge expired ones. Note that snapshots are not atomic relative to one another.
	
+ --prune-snapshots

	This will process your sanoid.conf file, it will NOT create snapshots, but it will purge expired ones.
	
+ --monitor-snapshots

	This option is designed to be run by a Nagios monitoring system. It reports on the health of your snapshots.
	
+ --monitor-health

	This option is designed to be run by a Nagios monitoring system. It reports on the health of the zpool your filesystems are on. It only monitors filesystems that are configured in the sanoid.conf file.
	
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

##### Syncoid Command Line Options

+ --[source]

	This is the source dataset. It can be either local or remote.

+ --[destination]

	This is the destination dataset. It can be either local or remote.

+ -r --recursive

	This will also transfer child datasets.

+ --compress <compression type>

	Currently accepts gzip and lzo. lzo is fast and light on the processsor and is the default. If the selected compression method is unavailable on the source and destination, no compression will be used.

+ --source-bwlimit <limit t|g|m|k>

	This is the bandwidth limit imposed upon the source. This is mainly used if the target does not have mbuffer installed, but bandwidth limites are desired.

+ --target-bw-limit <limit t|g|m|k>

	This is the bandwidth limit imposed upon the target. This is mainly used if the source does not have mbuffer installed, but bandwidth limites are desired.

+ --nocommandchecks

	Do not check the existance of commands before attempting the transfer. It assumes all programs are available. This should never be used.

+ --no-stream

	This argument tells syncoid to use -i incrementals, not -I. This updates the target with the newest snapshot from the source, without replicating the intermediate snapshots in between. (If used for an initial synchronization, will do a full replication from newest snapshot and exit immediately, rather than starting with the oldest and then doing an immediate -i to the newest.)

+ --no-sync-snap

	This argument tells syncoid to restrict itself to existing snapshots, instead of creating a semi-ephemeral syncoid snapshot at execution time. Especially useful in multi-target (A->B, A->C) replication schemes, where you might otherwise accumulate a large number of foreign syncoid snapshots.

+ --dumpsnaps

	This prints a list of snapshots during the run.

+ --sshport

	Allow sync to/from boxes running SSH on non-standard ports.

+ --sshkey

	Use specified identity file as per ssh -i.

+ --quiet

	Supress non-error output.	

+ --verbose

	This prints additional information during the sanoid run.

+ --debug

	This prints out quite alot of additional information during a sanoid run, and is normally not needed.

+ --version

	Print the version and exit.

+ --monitor-version

	This doesn't do anything right now.

Note that the snapshots it takes and transfers are not atomic relative to one another
