#!/bin/sh

# Функция очистки временной директории
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Обработка сигналов
trap cleanup INT TERM EXIT

# Проверка наличия входного файла
if [ $# -ne 1 ]; then
    echo "Использование: $0 <исходный файл>"
    exit 1
fi

SOURCE_FILE="$1"

# Проверка существования файла
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Ошибка: файл '$SOURCE_FILE' не существует"
    exit 2
fi

# Создание временной директории
TEMP_DIR=$(mktemp -d)
if [ $? -ne 0 ]; then
    echo "Ошибка: не удалось создать временную директорию"
    exit 3
fi

# Сохраняем исходную директорию перед переходом во временную
ORIGINAL_DIR="$(cd "$(dirname "$SOURCE_FILE")" && pwd)"

# Копирование исходного файла во временную директорию
cp "$SOURCE_FILE" "$TEMP_DIR/"

# Получение имени выходного файла из комментария
OUTPUT_FILE=$(grep -o "&Output:.*" "$SOURCE_FILE" | cut -d: -f2- | tr -d ' ')
if [ -z "$OUTPUT_FILE" ]; then
    echo "Ошибка: не найден комментарий с выходным файлом (&Output:)"
    exit 4
fi

cd "$TEMP_DIR"

# Определение типа файла и его компиляция
case "$SOURCE_FILE" in
    *.c)
        gcc "${SOURCE_FILE##*/}" -o "$OUTPUT_FILE" 2>/dev/null
        COMPILE_STATUS=$?
        ;;
    *.cpp)
        g++ "${SOURCE_FILE##*/}" -o "$OUTPUT_FILE" 2>/dev/null
        COMPILE_STATUS=$?
        ;;
    *.tex)
        pdflatex "${SOURCE_FILE##*/}" >/dev/null 2>&1
        COMPILE_STATUS=$?
        ;;
    *)
        echo "Ошибка: неподдерживаемый тип файла"
        exit 5
        ;;
esac

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "Ошибка: не удалось скомпилировать файл"
    exit 6
fi

# Копирование результата в исходную директорию
if [ -f "$OUTPUT_FILE" ]; then
    mv "$OUTPUT_FILE" "$ORIGINAL_DIR/"
    chmod +x "$ORIGINAL_DIR/$OUTPUT_FILE"
    
    # Возвращаемся в исходную директорию
    cd "$ORIGINAL_DIR"
    echo "Сборка успешно завершена. Создан файл: $OUTPUT_FILE"
else
    echo "Ошибка: выходной файл не создан"
    exit 7
fi

exit 0 