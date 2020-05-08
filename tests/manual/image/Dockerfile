FROM puremourning/vimspector:test

RUN apt-get update && \
  apt-get -y dist-upgrade && \
  apt-get -y install sudo

## cleanup of files from setup
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN useradd -ms /bin/bash -d /home/dev -G sudo dev && \
    echo "dev:dev" | chpasswd && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/sudo

USER dev
WORKDIR /home/dev

ENV HOME /home/dev
ENV PYTHON_CONFIGURE_OPTS --enable-shared
ENV VIMSPECTOR_MIMODE gdb
ENV GOPATH /home/dev/go

RUN eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv) && \
    go get -u github.com/go-delve/delve/cmd/dlv

ADD --chown=dev:dev .vim/ /home/dev/.vim/
