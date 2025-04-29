#!/bin/bash

# Остановить и удалить все существующие контейнеры
echo "Останавливаю и удаляю все контейнеры..."
sudo docker stop $(sudo docker ps -a -q) 2>/dev/null || true
sudo docker rm $(sudo docker ps -a -q) 2>/dev/null || true

# Удалить volume
echo "Удаляю volume..."
sudo docker volume rm shared_volume 2>/dev/null || true

# Создать новый volume
echo "Создаю новый volume..."
sudo docker volume create shared_volume

# Пересобрать образ
echo "Пересобираю образ..."
sudo docker build -t concurrent-container .

# Запустить новые контейнеры
echo "Запускаю контейнеры..."
for i in $(seq 1 ${1:-3})
do
    sudo docker run -d --name concurrent-container-$i \
        -v shared_volume:/shared concurrent-container
    echo "Контейнер $i запущен"
done

# Проверить, что контейнеры запущены
echo "Список запущенных контейнеров:"
sudo docker ps --filter ancestor=concurrent-container

echo "Для просмотра логов используйте:"
for i in $(seq 1 ${1:-3})
do
    echo "sudo docker logs -f concurrent-container-$i"
done