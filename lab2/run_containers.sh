#!/bin/sh

# Создание образа
docker build -t concurrent-container .

# Создание общего тома
docker volume create shared_volume

# Остановка и удаление контейнеров по имени
echo "Очистка существующих контейнеров..."
for i in $(seq 1 10); do
    docker stop concurrent-container-$i 2>/dev/null || true
    docker rm concurrent-container-$i 2>/dev/null || true
done

# Запуск контейнеров (по умолчанию 1)
CONTAINER_COUNT=${1:-1}

echo "Запуск $CONTAINER_COUNT контейнеров..."

for i in $(seq 1 $CONTAINER_COUNT); do
    docker run -d --name concurrent-container-$i -v shared_volume:/shared concurrent-container
done

echo "Контейнеры запущены. Для просмотра логов используйте:"
echo "docker logs concurrent-container-1"
echo "Для просмотра всех файлов в общем томе:"
echo "docker exec concurrent-container-1 ls -la /shared"
echo "Для остановки всех контейнеров используйте:"
echo "docker stop \$(docker ps -q --filter ancestor=concurrent-container)"