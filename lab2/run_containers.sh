#!/bin/bash

# Остановить и удалить все существующие контейнеры
echo "Останавливаю и удаляю все контейнеры..."
docker container stop $(docker container ls -aq) 2>/dev/null || true
docker container rm $(docker container ls -aq) 2>/dev/null || true

# Удалить volume
echo "Удаляю volume..."
docker volume rm shared_volume 2>/dev/null || true

# Создать новый volume
echo "Создаю новый volume..."
docker volume create shared_volume

# Пересобрать образ
echo "Пересобираю образ..."
docker build -t concurrent-container .

# Запустить новые контейнеры
echo "Запускаю контейнеры..."
for i in $(seq 1 ${1:-3})
do
    docker container run -d --name concurrent-container-$i \
        -v shared_volume:/shared concurrent-container
    echo "Контейнер $i запущен"
done

# Проверить, что контейнеры запущены
echo "Список запущенных контейнеров:"
docker container ls --filter ancestor=concurrent-container

# Очистка неиспользуемых ресурсов
docker container prune -f  # удаляет остановленные контейнеры
docker image prune -f      # удаляет неиспользуемые образы

echo "Для просмотра логов используйте:"
for i in $(seq 1 ${1:-3})
do
    echo "sudo docker logs -f concurrent-container-$i"
done