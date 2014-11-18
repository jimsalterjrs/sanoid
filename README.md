sanoid
======

Sanoid is a policy-driven snapshot management tool for ZFS filesystems.

You can use Sanoid to create, automatically thin, and monitor snapshots and pool health from a single eminently human-readable TOML config file at /etc/sanoid/sanoid.conf.  A typical Sanoid system would have a single cron job:

```
* * * * * /usr/local/bin/sanoid --cron
```

And its /etc/sanoid/sanoid.conf might look something like this:

```
[data/home]
	use_template = production
[data/images/win2012]
	use_template = production
[data/images/win7-spice]
	use_template = production
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

Which would be enough to tell sanoid to take and keep 36 hourly snapshots, 30 dailies, 3 monthlies, and no yearlies.  Except in the case of data/images/win7-spice, which only keeps 4 hourlies for whatever reason.

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

Syncoid supports and uses mbuffer buffering, lzop compression, and pv progress bars if the utilities are available on the systems used.
