#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def get_stats():
    """Получает статистику сервиса"""
    try:
        # Статистика анализа
        stats_response = requests.get(f"{BASE_URL}/stats", timeout=5)
        stats = stats_response.json() if stats_response.status_code == 200 else {}
        
        # Статус очереди
        queue_response = requests.get(f"{BASE_URL}/queue_status", timeout=5)
        queue_status = queue_response.json() if queue_response.status_code == 200 else {}
        
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "stats": stats,
            "queue": queue_status
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "error": str(e)
        }

def monitor_service(interval=5):
    """Мониторинг сервиса в реальном времени"""
    print("📊 МОНИТОРИНГ СЕРВИСА URL ANALYZER")
    print("=" * 60)
    print("Нажмите Ctrl+C для остановки")
    print("-" * 60)
    
    try:
        while True:
            data = get_stats()
            
            if "error" in data:
                print(f"[{data['timestamp']}] ❌ Ошибка: {data['error']}")
            else:
                stats = data.get("stats", {})
                queue = data.get("queue", {})
                
                total_analyzed = stats.get("total_analyzed", 0)
                queue_length = queue.get("queue_length", 0)
                pending_results = queue.get("pending_results", 0)
                
                # Статистика безопасности
                security_stats = stats.get("security_stats", {})
                secure = security_stats.get("secure", 0)
                insecure = security_stats.get("insecure", 0)
                
                print(f"[{data['timestamp']}] "
                      f"Проанализировано: {total_analyzed} | "
                      f"Очередь: {queue_length} | "
                      f"Ожидают: {pending_results} | "
                      f"HTTPS: {secure}/{secure+insecure if secure+insecure > 0 else 0}")
                
                # Показываем топ доменных зон каждые 30 секунд
                if int(time.time()) % 30 == 0:
                    tld_dist = stats.get("tld_distribution", {})
                    if tld_dist:
                        top_tlds = sorted(tld_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                        print(f"    Топ доменов: {', '.join([f'{tld}({count})' for tld, count in top_tlds])}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Мониторинг остановлен")

if __name__ == "__main__":
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    monitor_service(interval) 