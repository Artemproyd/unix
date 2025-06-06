#!/usr/bin/env python3

import json
import uuid
import time
import hashlib
from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
from threading import Thread, Lock
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
producer = None
results = {}
worker_status = {}  # Статус worker'ов
kafka_connected = False
status_lock = Lock()

def init_kafka():
    global producer, kafka_connected
    logger.info("🔧 Connecting to Kafka...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            # Проверяем доступность Kafka
            test_producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=10000,
                retry_backoff_ms=1000
            )
            test_producer.close()
            
            # Создаем основной producer с ключами для балансировки
            producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                request_timeout_ms=10000,
                retry_backoff_ms=1000
            )
            
            # Запускаем consumer в отдельном потоке
            Thread(target=consume_results, daemon=True).start()
            
            kafka_connected = True
            logger.info("✅ Kafka connected successfully")
            return True
            
        except Exception as e:
            logger.warning(f"❌ Attempt {attempt+1}/{max_attempts}: {e}")
            time.sleep(5)
    
    logger.error("❌ Failed to connect to Kafka after all attempts")
    return False

def consume_results():
    global kafka_connected
    max_attempts = 10
    
    for attempt in range(max_attempts):
        try:
            consumer = KafkaConsumer(
                'results',
                bootstrap_servers=['kafka:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                group_id='gateway-consumer'
            )
            
            logger.info("✅ Result consumer started")
            
            for msg in consumer:
                data = msg.value
                
                # Обрабатываем worker status уведомления
                if data.get('type') == 'worker_status':
                    handle_worker_status(data)
                elif 'task_id' in data:
                    # Обычные результаты задач
                    results[data['task_id']] = data
                    logger.info(f"📥 Got result for: {data['task_id']}")
                    
        except Exception as e:
            logger.error(f"❌ Consumer error (attempt {attempt+1}): {e}")
            time.sleep(5)
            
    logger.error("❌ Consumer failed after all attempts")

def handle_worker_status(status_data):
    """Обработка уведомлений о статусе worker'ов"""
    worker_id = status_data.get('worker_id')
    status = status_data.get('status')
    timestamp = status_data.get('timestamp')
    current_task = status_data.get('current_task')
    
    with status_lock:
        if worker_id not in worker_status:
            worker_status[worker_id] = {}
            
        worker_status[worker_id].update({
            'status': status,
            'last_update': timestamp,
            'current_task': current_task
        })
    
    # Логируем важные события
    if status == 'worker_started':
        logger.info(f"🚀 Worker {worker_id} started")
    elif status == 'shutdown_started':
        logger.info(f"🛑 Worker {worker_id} beginning graceful shutdown (current task: {current_task})")
    elif status == 'shutdown_completed':
        logger.info(f"👋 Worker {worker_id} completed graceful shutdown")

@app.route('/analyze', methods=['POST'])
def analyze():
    if not kafka_connected or not producer:
        return jsonify({"error": "Kafka not available", "connected": kafka_connected}), 503
    
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Text required"}), 400
    
    task_id = str(uuid.uuid4())
    task = {"task_id": task_id, "text": data['text']}
    
    partition_key = hashlib.md5(task_id.encode()).hexdigest()[:8]
    
    try:
        logger.info(f"📤 Sending task: {task_id} with key: {partition_key}")
        producer.send('tasks', value=task, key=partition_key)
        producer.flush()
        
        # Ждем результат с увеличенным timeout
        for _ in range(100):  
            if task_id in results:
                result = results.pop(task_id)
                logger.info(f"✅ Returning result: {task_id}")
                return jsonify(result)
            time.sleep(0.1)
        
        logger.warning(f"⏰ Timeout for: {task_id}")
        return jsonify({"error": "Processing timeout"}), 408
        
    except Exception as e:
        logger.error(f"❌ Error processing task {task_id}: {e}")
        return jsonify({"error": "Internal error"}), 500

@app.route('/workers/status')
def workers_status():
    """Получение статуса всех worker'ов"""
    with status_lock:
        current_time = int(time.time())
        workers_info = {}
        
        for worker_id, info in worker_status.items():
            last_update = info.get('last_update', 0)
            time_since_update = current_time - last_update
            
            workers_info[worker_id] = {
                'status': info.get('status', 'unknown'),
                'current_task': info.get('current_task'),
                'last_update': last_update,
                'seconds_since_update': time_since_update,
                'is_responsive': time_since_update < 60  # считаем worker активным если обновление было менее минуты назад
            }
    
    active_workers = sum(1 for w in workers_info.values() if w['is_responsive'])
    shutting_down = sum(1 for w in workers_info.values() if 'shutdown' in w['status'])
    
    return jsonify({
        "total_workers": len(workers_info),
        "active_workers": active_workers,
        "shutting_down_workers": shutting_down,
        "workers": workers_info
    })

@app.route('/health')
def health():
    with status_lock:
        active_workers = sum(1 for info in worker_status.values() 
                           if (int(time.time()) - info.get('last_update', 0)) < 60)
    
    return jsonify({
        "status": "ok" if kafka_connected else "error",
        "kafka_connected": kafka_connected,
        "producer_ready": producer is not None,
        "active_workers": active_workers
    })

if __name__ == '__main__':
    # Запускаем подключение к Kafka в отдельном потоке
    Thread(target=init_kafka, daemon=True).start()
    
    # Ждем немного для инициализации
    time.sleep(5)
    
    app.run(host='0.0.0.0', port=8080, debug=False) 