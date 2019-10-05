# Sanoid Docker Image

All the commands below are executed in the **docker** directory which contains the **docker-compose.yml** file.  It is assumed that you have [Docker Compose](https://docs.docker.com/compose/) already installed on your system.

## Building the Image
```bash
docker-compose build
```

## Usage

Place your **sanoid.conf** in the **docker** directory.

Before the first run, SSH keys need to be generated and copied to the target server.

```bash
docker-compose run --rm sanoid ssh-keygen
docker-compose run --rm sanoid ssh-copy-id syncoid_user@target_server
```

You are now ready to go. The default command for the container is **sanoid** so the following commands are equivalent:
```bash
docker-compose run --rm sanoid
docker-compose run --rm sanoid sanoid
```

To run **syncoid**, run the following:
```bash
docker-compose run --rm sanoid syncoid tank/foo synncoid_user@target_server:tank/foo
```

## Tips

### Allow syncoid to execute ZFS without a password on the target server

On the target server:
```bash
sudo visudo
```

Then add the following to end of the file:

```
syncoid_user ALL=(ALL:ALL) NOPASSWD: /sbin/zfs
```
Reference: https://www.reddit.com/r/zfs/comments/3259gb/sanoidsyncoid_support_thread/
