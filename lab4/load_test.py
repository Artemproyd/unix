#!/usr/bin/env python3

import requests
import threading
import time
import random

def send_request(i):
    try:
        # Разные тексты для разного хеширования
        texts = [
            f"Первый тест {i} для балансировки нагрузки",
            f"Второй вариант текста номер {i} с другим содержимым", 
            f"Третий текст задачи {i} совершенно иной по структуре",
            f"Четвертый вид сообщения {i} для проверки распределения",
            f"Пятый тип контента {i} уникальный по своей сути"
        ]
        text = random.choice(texts)
        
        r = requests.post("http://localhost:8080/analyze", json={"text": text})
        data = r.json()
        if data.get('success'):
            print(f"✅ Задача {i}: '{text[:20]}...' → {data['processed_by']}")
        else:
            print(f"❌ Задача {i}: ошибка - {data.get('error')}")
    except Exception as e:
        print(f"❌ Задача {i}: {e}")

print("🚀 АГРЕССИВНЫЙ нагрузочный тест...")

# Отправляем 50 задач ОЧЕНЬ быстро
threads = []
for i in range(50):
    t = threading.Thread(target=send_request, args=(i,))
    threads.append(t)
    t.start()
    time.sleep(0.01)  # ОЧЕНЬ быстро!

# Ждем завершения всех потоков
for t in threads:
    t.join()

print("✅ Тест завершен - проверяем распределение!") 