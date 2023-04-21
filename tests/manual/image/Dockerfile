ARG ARCH=x86_64

FROM puremourning/vimspector:test-${ARCH}

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

ENV VIMSPECTOR_TEST_BASE test-base-linux
ENV TEST_NO_RETRY 1

RUN go install github.com/go-delve/delve/cmd/dlv@latest

ADD --chown=dev:dev .vim/ /home/dev/.vim/
RUN mkdir -p /home/dev/.config/nvim && \
    cd /home/dev/.config/nvim && \
    ln -s /home/dev/.vim/vimrc init.vim
