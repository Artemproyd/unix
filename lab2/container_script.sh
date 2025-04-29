#!/bin/bash

# Генерация уникального ID контейнера
CONTAINER_ID=$(hostname | cut -c1-4)
echo "Контейнер $CONTAINER_ID начал работу"

# Создаем директорию shared, если её нет
mkdir -p /shared
touch /shared/.lock

# Счетчик операций
COUNTER=0

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
        LAST_FILE=$(ls -1 /shared/[0-9][0-9][0-9] 2>/dev/null | sort -n | tail -n 1)
        if [ -z "$LAST_FILE" ]; then
            # Если файлов нет, начинаем с 001
            i="001"
        else
            # Берем следующий номер после последнего существующего
            i=$(printf "%03d" $((10#${LAST_FILE##*/} + 1)))
        fi
        
        echo "$CONTAINER_ID:$COUNTER" > "/shared/$i"
        echo "[$CONTAINER_ID] Создал файл $i (операция $COUNTER)"
    ) 200>/shared/.lock
    
    # Пауза ровно 1 секунда между операциями
    sleep 1
    
    # Удаление файла (атомарная операция)
    (
        # Получаем блокировку
        flock -x 200
        
        # Ищем свой файл для удаления
        for file in /shared/[0-9][0-9][0-9]
        do
            if [ -f "$file" ] && grep -q "^$CONTAINER_ID:" "$file" 2>/dev/null; then
                echo "[$CONTAINER_ID] Удаляю файл $file"
                rm "$file"
                break
            fi
        done
    ) 200>/shared/.lock
    
    # Пауза ровно 1 секунда между операциями
    sleep 1
done