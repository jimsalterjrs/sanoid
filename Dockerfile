FROM ubuntu:bionic-20190912.1

LABEL maintainer="King Ramos <rkramos@yahoo.com>"

RUN apt update && apt install -y \
    curl \
    libcapture-tiny-perl \
    libconfig-inifiles-perl \
    lzop \
    mbuffer \
    pv \
    ssh-client \
    zfsutils-linux \
    && rm -rf /var/lib/apt/lists/*

COPY sanoid /usr/local/bin/
COPY sanoid.defaults.conf /etc/sanoid/

COPY syncoid /usr/local/bin/

CMD [ "sanoid" ]