#!/bin/sh
# Генерация ID
CONTAINER_ID=$(head -c 8 /dev/urandom | tr -dc 'a-zA-Z0-9')
echo "Контейнер запущен с ID: $CONTAINER_ID"

# Файл блокировки
LOCK_FILE="/shared/.lock"
touch "$LOCK_FILE"

# Счетчик файлов
FILE_COUNTER=0

while true
do
  # Создание файла с блокировкой
  flock -x "$LOCK_FILE" sh -c '
    # Поиск свободного имени
    FILE_NUM=1
    while [ $FILE_NUM -lt 1000 ]
    do
      if [ $FILE_NUM -lt 10 ]
      then
        FILE_NAME="00$FILE_NUM"
      elif [ $FILE_NUM -lt 100 ]
      then
        FILE_NAME="0$FILE_NUM"
      else
        FILE_NAME="$FILE_NUM"
      fi
      
      if [ ! -f "/shared/$FILE_NAME" ]
      then
        break
      fi
      
      FILE_NUM=$((FILE_NUM + 1))
    done
    
    # Создаем файл
    FILE_COUNTER=$(('"$FILE_COUNTER"' + 1))
    echo "'"$CONTAINER_ID"':$FILE_COUNTER" > "/shared/$FILE_NAME"
    echo "Создан файл: $FILE_NAME с содержимым '"$CONTAINER_ID"':$FILE_COUNTER"
  '
  
  sleep 1
  
  # Удаление файла с блокировкой
  flock -x "$LOCK_FILE" sh -c '
    # Поиск файла для удаления
    for FILE in /shared/[0-9][0-9][0-9]
    do
      if grep -q "'"$CONTAINER_ID"'" "$FILE" 2>/dev/null
      then
        LAST_FILE="$FILE"
      fi
    done
    
    if [ -n "$LAST_FILE" ]
    then
      echo "Удаляем файл: $LAST_FILE"
      rm "$LAST_FILE"
    fi
  '
  
  sleep 1
done