FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    util-linux \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

COPY container_script.sh /usr/local/bin/container_script.sh
RUN chmod +x /usr/local/bin/container_script.sh

WORKDIR /shared

CMD ["/usr/local/bin/container_script.sh"] 