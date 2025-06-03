#!/usr/bin/env python3

import json
import re
import socket
import time
import logging
import random
from collections import Counter
from kafka import KafkaConsumer, KafkaProducer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_text(text):
    words = re.findall(r'\w+', text.lower())
    letters = re.findall(r'[a-zа-яё]', text.lower())
    
    return {
        "chars": len(text),
        "words": len(words),
        "unique_words": len(set(words)),
        "letters": len(letters),
        "top_words": dict(Counter(words).most_common(3)),
        "top_letters": dict(Counter(letters).most_common(3)),
        "processed_by": socket.gethostname(),
        "success": True
    }

def main():
    worker_id = socket.gethostname()
    # ВАЖНО: Уникальный group_id для каждого worker'а!
    unique_group = f"workers-{worker_id}-{random.randint(1000, 9999)}"
    
    logger.info(f"🔧 Worker {worker_id} starting with group: {unique_group}")
    
    max_attempts = 20
    for attempt in range(max_attempts):
        try:
            # Подключаемся к Kafka с уникальной группой
            consumer = KafkaConsumer(
                'tasks',
                bootstrap_servers=['kafka:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=unique_group,  # УНИКАЛЬНАЯ ГРУППА!
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            
            producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=10000,
                retry_backoff_ms=1000
            )
            
            logger.info(f"✅ Worker {worker_id} connected to Kafka with group {unique_group}")
            
            # Основной цикл обработки
            for msg in consumer:
                try:
                    task = msg.value
                    logger.info(f"📝 Worker {worker_id} processing: {task['text'][:30]}...")
                    
                    result = analyze_text(task['text'])
                    result['task_id'] = task['task_id']
                    
                    producer.send('results', result)
                    producer.flush()
                    
                    logger.info(f"✅ Worker {worker_id} completed task {task['task_id']}")
                    
                except Exception as e:
                    logger.error(f"❌ Worker {worker_id} task error: {e}")
                    
        except Exception as e:
            logger.warning(f"❌ Worker {worker_id} connection error (attempt {attempt+1}): {e}")
            time.sleep(5)
            
    logger.error(f"❌ Worker {worker_id} failed after all attempts")

if __name__ == '__main__':
    main() 