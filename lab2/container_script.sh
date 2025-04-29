#!/bin/bash

# Генерация уникального ID контейнера
CONTAINER_ID=$(hostname | cut -c1-4)
echo "Контейнер $CONTAINER_ID начал работу"

# Создаем директорию shared, если её нет
mkdir -p /shared
touch /shared/.lock

# Счетчик операций
COUNTER=0
CURRENT_FILE=""

# Функция для безопасного завершения
cleanup() {
    echo "[$CONTAINER_ID] Завершение работы..."
    exit 0
}

# Перехватываем сигналы
trap cleanup SIGINT SIGTERM

# Бесконечный цикл
while true
do
    COUNTER=$((COUNTER + 1))
    
    # Создание файла (атомарная операция)
    (
        # Получаем блокировку
        flock -x 200
        
        # Ищем первое свободное имя файла
        for i in $(seq -f "%03g" 1 999)
        do
            if [ ! -f "/shared/$i" ]; then
                echo "$CONTAINER_ID:$COUNTER" > "/shared/$i"
                CURRENT_FILE="/shared/$i"
                echo "[$CONTAINER_ID] Создал файл $i (операция $COUNTER)"
                break
            fi
        done
    ) 200>/shared/.lock
    
    # Пауза ровно 1 секунда между операциями
    sleep 1
    
    # Удаление файла (атомарная операция)
    (
        # Получаем блокировку
        flock -x 200
        
        if [ -f "$CURRENT_FILE" ]; then
            echo "[$CONTAINER_ID] Удаляю файл $CURRENT_FILE"
            rm "$CURRENT_FILE"
        fi
    ) 200>/shared/.lock
    
    # Пауза ровно 1 секунда между операциями
    sleep 1
done