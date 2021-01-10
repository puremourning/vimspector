FROM ubuntu:18.04

RUN apt-get update && \
  apt-get -y dist-upgrade && \
  apt-get -y install sudo \
                     lsb-release \
                     ca-certificates \
                     python3-dev \
                     python3-pip \
                     ca-cacert \
                     locales \
                     language-pack-en \
                     libncurses5-dev libncursesw5-dev \
                     git && \
  apt-get -y autoremove

## cleanup of files from setup
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install debugpy

ADD main.py /root/main.py
