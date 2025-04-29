FROM ubuntu:20.04

# Установка необходимых пакетов
RUN apt-get update && \
    apt-get install -y util-linux coreutils bash procps grep && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копирование скрипта
COPY container_script.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/container_script.sh

# Запуск скрипта
ENTRYPOINT ["/bin/bash", "/usr/local/bin/container_script.sh"] 