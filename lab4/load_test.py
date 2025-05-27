#!/usr/bin/env python3
import requests
import json
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# Список тестовых URL для анализа
TEST_URLS = [
    "https://www.google.com",
    "https://github.com/user/repo",
    "https://stackoverflow.com/questions/123",
    "https://www.youtube.com/watch?v=abc123",
    "https://facebook.com/page",
    "https://twitter.com/user",
    "https://linkedin.com/in/user",
    "https://instagram.com/user",
    "http://suspicious-site.tk/malware",
    "https://example.com/very/long/path/with/many/segments",
    "https://test.com?param1=value1&param2=value2&param3=value3",
    "https://192.168.1.1:8080/admin",
    "https://sub.domain.example.org/path",
    "https://очень-длинный-домен-с-кириллицей.рф/путь"
]

BASE_URL = "http://localhost:5000"

def send_request(url):
    """Отправляет один запрос на анализ URL"""
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/analyze_url",
            json={"url": url},
            timeout=35
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            "url": url,
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 200,
            "error": None if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": 0,
            "response_time": 0,
            "success": False,
            "error": str(e)
        }

def get_queue_status():
    """Получает статус очереди"""
    try:
        response = requests.get(f"{BASE_URL}/queue_status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"queue_length": "unknown", "pending_results": "unknown"}

def load_test(num_requests=50, num_threads=10):
    """Выполняет нагрузочное тестирование"""
    print(f"🚀 Запуск нагрузочного тестирования:")
    print(f"   Количество запросов: {num_requests}")
    print(f"   Количество потоков: {num_threads}")
    print(f"   Целевой URL: {BASE_URL}")
    print("-" * 50)
    
    # Проверяем доступность сервиса
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Сервис недоступен!")
            return
        print("✅ Сервис доступен")
    except:
        print("❌ Не удается подключиться к сервису!")
        return
    
    # Генерируем список URL для тестирования
    test_urls = [random.choice(TEST_URLS) for _ in range(num_requests)]
    
    results = []
    start_time = time.time()
    
    # Выполняем запросы в многопоточном режиме
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Отправляем все задачи
        future_to_url = {executor.submit(send_request, url): url for url in test_urls}
        
        completed = 0
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            completed += 1
            
            # Показываем прогресс каждые 10 запросов
            if completed % 10 == 0 or completed == num_requests:
                queue_status = get_queue_status()
                print(f"Выполнено: {completed}/{num_requests} | "
                      f"Очередь: {queue_status['queue_length']} | "
                      f"Ожидающие: {queue_status['pending_results']}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Анализируем результаты
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        response_times = [r['response_time'] for r in successful]
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
    else:
        avg_response_time = min_response_time = max_response_time = 0
    
    # Выводим статистику
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print(f"Общее время выполнения: {total_time:.2f} сек")
    print(f"Запросов в секунду: {num_requests/total_time:.2f}")
    print(f"Успешных запросов: {len(successful)}/{num_requests} ({len(successful)/num_requests*100:.1f}%)")
    print(f"Неудачных запросов: {len(failed)}")
    
    if successful:
        print(f"\nВремя отклика:")
        print(f"  Среднее: {avg_response_time:.2f} сек")
        print(f"  Минимальное: {min_response_time:.2f} сек")
        print(f"  Максимальное: {max_response_time:.2f} сек")
    
    if failed:
        print(f"\nОшибки:")
        error_types = {}
        for f in failed:
            error = f['error'] or f"HTTP {f['status_code']}"
            error_types[error] = error_types.get(error, 0) + 1
        
        for error, count in error_types.items():
            print(f"  {error}: {count}")
    
    # Финальный статус очереди
    final_queue_status = get_queue_status()
    print(f"\nФинальное состояние очереди:")
    print(f"  Задач в очереди: {final_queue_status['queue_length']}")
    print(f"  Ожидающих результатов: {final_queue_status['pending_results']}")

def stress_test():
    """Стресс-тестирование с постепенным увеличением нагрузки"""
    print("🔥 СТРЕСС-ТЕСТИРОВАНИЕ")
    print("=" * 50)
    
    test_configs = [
        (10, 2),   # 10 запросов, 2 потока
        (25, 5),   # 25 запросов, 5 потоков
        (50, 10),  # 50 запросов, 10 потоков
        (100, 20), # 100 запросов, 20 потоков
    ]
    
    for requests_count, threads_count in test_configs:
        print(f"\n🧪 Тест: {requests_count} запросов, {threads_count} потоков")
        load_test(requests_count, threads_count)
        print("\nОжидание 5 секунд перед следующим тестом...")
        time.sleep(5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "stress":
            stress_test()
        elif sys.argv[1] == "quick":
            load_test(20, 5)
        else:
            try:
                requests = int(sys.argv[1])
                threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                load_test(requests, threads)
            except:
                print("Использование: python load_test.py [stress|quick|<количество_запросов> [<количество_потоков>]]")
    else:
        load_test()  # Стандартный тест: 50 запросов, 10 потоков 