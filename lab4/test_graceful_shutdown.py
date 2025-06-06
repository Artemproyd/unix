#!/usr/bin/env python3

import requests
import time
import json
import subprocess
import signal
import threading

def send_analyze_request(text, request_id):
    """Отправляем запрос на анализ текста"""
    try:
        response = requests.post('http://localhost:8080/analyze', 
                               json={'text': text}, 
                               timeout=15)
        print(f"🔄 Request {request_id}: {response.status_code} - {response.json()}")
        return response.json()
    except Exception as e:
        print(f"❌ Request {request_id} failed: {e}")
        return None

def monitor_workers():
    """Мониторим статус worker'ов"""
    try:
        response = requests.get('http://localhost:8080/workers/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Workers Status:")
            print(f"   Total: {data['total_workers']}, Active: {data['active_workers']}, Shutting down: {data['shutting_down_workers']}")
            
            for worker_id, info in data['workers'].items():
                status_emoji = "🟢" if info['is_responsive'] else "🔴"
                current_task = f"(task: {info['current_task']})" if info['current_task'] else ""
                print(f"   {status_emoji} {worker_id}: {info['status']} {current_task}")
        else:
            print(f"❌ Failed to get workers status: {response.status_code}")
    except Exception as e:
        print(f"❌ Monitor error: {e}")

def load_generator():
    """Генерируем постоянную нагрузку"""
    texts = [
        "Это тестовый текст для анализа системы graceful shutdown",
        "Проверяем как работает корректное завершение работы контейнеров",
        "Lorem ipsum dolor sit amet consectetur adipiscing elit",
        "Системы горизонтального масштабирования должны корректно обрабатывать shutdown",
        "Тестируем балансировку нагрузки и отказоустойчивость сервиса"
    ]
    
    request_id = 1
    while True:
        try:
            text = texts[(request_id - 1) % len(texts)]
            threading.Thread(target=send_analyze_request, 
                           args=(f"{text} (request #{request_id})", request_id)).start()
            request_id += 1
            time.sleep(2)  # Отправляем запрос каждые 2 секунды
        except KeyboardInterrupt:
            print("\n🛑 Load generator stopped")
            break

def main():
    print("🚀 Testing Graceful Shutdown")
    print("=" * 50)
    
    # Проверяем что сервисы запущены
    try:
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code != 200:
            print("❌ Gateway not responding, please start services first")
            return
        print("✅ Gateway is running")
    except:
        print("❌ Cannot connect to gateway, please start services first")
        return
    
    print("\n📊 Initial workers status:")
    monitor_workers()
    
    print(f"\n🔄 Starting load generation...")
    print("   Sending requests every 2 seconds")
    print("   While load is running, try these commands in another terminal:")
    print("   docker-compose stop worker  # Graceful shutdown")
    print("   docker-compose up -d --scale worker=3  # Scale up")
    print("   docker-compose up -d --scale worker=1  # Scale down")
    print("\n   Press Ctrl+C to stop load generation")
    
    # Запускаем мониторинг в отдельном потоке
    def monitor_loop():
        while True:
            time.sleep(5)
            monitor_workers()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    # Запускаем генератор нагрузки
    try:
        load_generator()
    except KeyboardInterrupt:
        print("\n👋 Test completed")

if __name__ == '__main__':
    main() 