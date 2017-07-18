# Syncoid-Rsync

What this is
------------

Syncoid-Rsync is a modification of the ZFS synchronization tool, syncoid, from the <a href="https://github.com/jimsalterjrs/sanoid">sanoid project</a>. This modification makes some significant changes to add a new mode of operation to syncoid that implements a form of "resume" support for ZFS send/receive operations. Please see the sanoid project page for more general information about the syncoid tool.

Who should use this
-------------------

If you find yourself needing to send large ZFS snapshots/filesystems over the internet, and can never successfully finish a particularly large send over the hours or days it might take, then this is for you. It solves all the "broken pipe" problems. You can even unplug the NIC on your server, go eat lunch, and then reconnect it without losing your progress.

Who should NOT use this
-----------------------

If you only use syncoid over LAN, please use the normal syncoid. Likewise, if you do send over WAN, but you don't have any issues with network disruption resetting your progress, then please use the normal syncoid.

Also of note - the way this modification operates is fairly complicated. It's definitely a KISS violation here, folks - it's not a simple source<->destination pipe like normal ZFS synchronization methods. Ie - there's much more room for errors. I've only tested it on my own servers, which are all running on proxmox-ve_4.4. It relies on standard unix utilities, and I've made efforts to add safety checks when anything potentially dangerous is being done (removing directories/etc), but YMMV on other platforms. Please only use this if you are willing/able to test it in a safe environment or review the code yourself before tossing valuable data against it. Or, you know, if you're adventurous.

What you need
-------------

Please see the INSTALL file for comments about the requirements, which are slightly different from the normal syncoid.

How to use it
-------------

Usage is the same as with regular syncoid (see the main syncoid project page for detailed usage instructions), but with a single added flag to make it operate in the new mode - "--rsync". This mode can currently only be used if either the source or destination is remote.

```
# Pull replication:

syncoid --rsync root@remotehost:data/images/vm backup/images/vm

# Push replication:

syncoid --rsync data/images/vm root@remotehost:backup/images/vm
```

If you leave off the --rsync flag then it will operate the same as the regular version.

How it works
------------

Without native send/receive resume support built into ZFS itself there's no way to avoid aborting a transfer when the network pipe established by SSH is interrupted for any reason, at any point over the duration of the send.

What this modification is doing to avoid that is to use helper daemons on the sending and receiving sides which communicate with the zfs send and zfs receive pipes, respectively. These daemons send and receive the data in discrete "chunks". The main script instance that you launch when you ran the command has its job to start the daemon processes, transfer the chunks, and coordinate cleanup and some communication between the sending and receiving daemons. This is all accomplished primarily with three new functions. With this setup, the sending and receiving pipes to ZFS are never broken (up to the inactivity timeout value you configure), so the send will survive even long periods of time with no internet, etc.

##### Main Script Responsibilities:

Beyond the normal syncoid responsibilities, the --rsync mode's loop in the main script:

+ Transfers itself to a randomized /tmp/syncoid-<randomsessionID>/ folder in the source and destination servers.
+ Calls itself as a background process in the source and destination servers with a special flag to put it into daemon mode.
+ Loops continuously, looking for and transferring the next expected chunk.
+ Transmits information from source to destination about ending conditions.
+ End daemons and clean up temp data when it gets information from the source and destination daemons that they are finished.
+ Abort if more than a configurable amount of time passes in which no progress is made.

##### Sending Daemon Responsibilities:

+ Establish a pipe to the ZFS Send process, optionally utilizing compression.
+ Receive a configurable amount of data from the pipe into memory, and then bundle it up as a "chunk"
+ MD5 checksum the chunk. The point of this when the ZFS stream itself is checksummed is that the "ZAP" objects are apparently not checksummed and, while extraordinarily rare, can lead to serious problems if corrupted and received via a send/receive operation. At typical WAN speeds, some additional checksumming has negligible CPU/IO impact.
+ Store the chunk and its MD5 in its /tmp folder
+ Clean up any old /tmp/syncoid-* folders which are not currently active and that were not cleaned up properly for whatever reason.
+ Abort if more than a configurable amount of time passes in which no progress is made.

##### Receiving Daemon Responsibilities:

+ Establish a pipe to the ZFS Receive process, optionally utilizing (de)compression.
+ As the main script transmits chunks, read them into memory, verify their MD5, and feed them into the pipe.
+ Close down gracefully once we finish the last chunk.
+ Clean up any old /tmp/syncoid-* folders which are not currently active and that were not cleaned up properly for whatever reason.
+ Abort if more than a configurable amount of time passes in which no progress is made.

What could be improved
----------------------

+ It assumes the utilities mentioned in INSTALL are in the system path on both ends. Verifying that would be good to do.
+ I tried to use ssh control sockets for this, but ran into issues (it not reestablishing itself after network interruptions, which is the whole point of this modification). So, I have this bypassing using control sockets if the --rsync flag is activated. Due to the extremely high number of ssh calls back and forth as this runs, it would be good if a more elegant way of doing this was implemented that didn't flood logs quite as much.
+ Some of the calls back and forth are just to communicate information between the sending and receiving daemons. I did this by sending files with the information back and forth because I'm lazy and didn't want to find a more elegant way. Maybe this could be done in a better way, though?
+ The "pv" utility can't be utilized in this mode, so the current "progress bar" is just a repeating line indicating the percent complete and the transmission speed of the last chunk transmitted. The percent can be quite off sometimes, however. I'm using the same estimation of the size that the normal syncoid utility uses, but my own large test send/receives can often be off by up to 40%. I think this might be due to ZFS filesystem compression not being factored into size estimate. Aside from the estimate being off, I'm sure someone could make a much prettier progress bar than this.
