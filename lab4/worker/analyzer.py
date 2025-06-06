#!/usr/bin/env python3

import json
import re
import socket
import time
import logging
import os
import signal
import threading
from collections import Counter
from kafka import KafkaConsumer, KafkaProducer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GracefulWorker:
    def __init__(self):
        self.worker_id = socket.gethostname()
        self.shutdown_requested = False
        self.current_task = None
        self.consumer = None
        self.producer = None
        self.lock = threading.Lock()
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info(f"🛑 Worker {self.worker_id} received {signal_name}, initiating graceful shutdown...")
        
        with self.lock:
            self.shutdown_requested = True
            
        # Отправляем уведомление о начале shutdown
        self._send_shutdown_notification("shutdown_started")
    
    def _send_shutdown_notification(self, status):
        """Отправляем уведомление о статусе shutdown"""
        try:
            if self.producer:
                notification = {
                    "type": "worker_status",
                    "worker_id": self.worker_id,
                    "status": status,
                    "timestamp": int(time.time()),
                    "current_task": self.current_task
                }
                
                self.producer.send('results', notification)
                self.producer.flush()
                logger.info(f"📡 Worker {self.worker_id} sent {status} notification")
        except Exception as e:
            logger.error(f"❌ Failed to send shutdown notification: {e}")

    def analyze_text(self, text):
        """Анализ текста"""
        words = re.findall(r'\w+', text.lower())
        letters = re.findall(r'[a-zа-яё]', text.lower())
        
        return {
            "chars": len(text),
            "words": len(words),
            "unique_words": len(set(words)),
            "letters": len(letters),
            "top_words": dict(Counter(words).most_common(3)),
            "top_letters": dict(Counter(letters).most_common(3)),
            "processed_by": self.worker_id,
            "success": True
        }

    def connect_to_kafka(self):
        """Подключение к Kafka с retry логикой"""
        startup_time = int(time.time() * 1000000)  
        process_id = os.getpid()
        unique_group = f"workers-{self.worker_id}-{process_id}-{startup_time}"
        
        logger.info(f"🔧 Worker {self.worker_id} starting with group: {unique_group}")
        
        max_attempts = 20
        for attempt in range(max_attempts):
            if self.shutdown_requested:
                logger.info(f"🛑 Worker {self.worker_id} shutdown requested during connection")
                return False
                
            try:
                # Подключаемся к Kafka с уникальной группой
                self.consumer = KafkaConsumer(
                    'tasks',
                    bootstrap_servers=['kafka:9092'],
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    group_id=unique_group,
                    auto_offset_reset='latest',
                    enable_auto_commit=False,  # Отключаем auto commit для контроля
                    consumer_timeout_ms=5000  # Timeout для проверки shutdown
                )
                
                self.producer = KafkaProducer(
                    bootstrap_servers=['kafka:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=10000,
                    retry_backoff_ms=1000
                )
                
                logger.info(f"✅ Worker {self.worker_id} connected to Kafka with group {unique_group}")
                return True
                
            except Exception as e:
                logger.warning(f"❌ Worker {self.worker_id} connection error (attempt {attempt+1}): {e}")
                time.sleep(5)
                
        logger.error(f"❌ Worker {self.worker_id} failed to connect after all attempts")
        return False

    def process_tasks(self):
        """Основной цикл обработки задач"""
        logger.info(f"🚀 Worker {self.worker_id} started processing tasks")
        
        try:
            while not self.shutdown_requested:
                try:
                    # Получаем сообщения с timeout для проверки shutdown
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_pack:
                        continue  # Нет новых сообщений, проверяем shutdown
                    
                    for topic_partition, messages in message_pack.items():
                        for msg in messages:
                            if self.shutdown_requested:
                                logger.info(f"🛑 Worker {self.worker_id} stopping - shutdown requested")
                                break
                                
                            try:
                                task = msg.value
                                task_id = task.get('task_id', 'unknown')
                                
                                with self.lock:
                                    self.current_task = task_id
                                
                                logger.info(f"📝 Worker {self.worker_id} processing task {task_id}: {task['text'][:30]}...")
                                
                                # Обрабатываем задачу
                                result = self.analyze_text(task['text'])
                                result['task_id'] = task_id
                                
                                # Отправляем результат
                                self.producer.send('results', result)
                                self.producer.flush()
                                
                                # Подтверждаем обработку сообщения
                                self.consumer.commit_async()
                                
                                logger.info(f"✅ Worker {self.worker_id} completed task {task_id}")
                                
                                with self.lock:
                                    self.current_task = None
                                    
                            except Exception as e:
                                logger.error(f"❌ Worker {self.worker_id} task error: {e}")
                                # В случае ошибки все равно commit чтобы не обрабатывать снова
                                self.consumer.commit_async()
                        
                        if self.shutdown_requested:
                            break
                            
                except Exception as e:
                    if not self.shutdown_requested:
                        logger.error(f"❌ Worker {self.worker_id} polling error: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id} fatal error: {e}")
        
        finally:
            self._cleanup()

    def _cleanup(self):
        """Корректное завершение работы"""
        logger.info(f"🧹 Worker {self.worker_id} starting cleanup...")
        
        # Ждем завершения текущей задачи
        if self.current_task:
            logger.info(f"⏳ Worker {self.worker_id} waiting for current task {self.current_task} to complete...")
            # Даем время на завершение текущей задачи (максимум 30 секунд)
            max_wait = 30
            waited = 0
            while self.current_task and waited < max_wait:
                time.sleep(1)
                waited += 1
                
            if self.current_task:
                logger.warning(f"⚠️ Worker {self.worker_id} forced to stop with unfinished task {self.current_task}")
        
        # Отправляем финальное уведомление
        self._send_shutdown_notification("shutdown_completed")
        
        # Закрываем соединения
        if self.consumer:
            try:
                self.consumer.close()
                logger.info(f"✅ Worker {self.worker_id} consumer closed")
            except Exception as e:
                logger.error(f"❌ Error closing consumer: {e}")
                
        if self.producer:
            try:
                self.producer.close()
                logger.info(f"✅ Worker {self.worker_id} producer closed")
            except Exception as e:
                logger.error(f"❌ Error closing producer: {e}")
        
        logger.info(f"👋 Worker {self.worker_id} gracefully shut down")

    def run(self):
        """Запуск worker'а"""
        logger.info(f"🚀 Starting graceful worker {self.worker_id}")
        
        if not self.connect_to_kafka():
            logger.error(f"❌ Worker {self.worker_id} failed to connect to Kafka")
            return
            
        # Отправляем уведомление о запуске
        self._send_shutdown_notification("worker_started")
        
        # Запускаем обработку задач
        self.process_tasks()

def main():
    worker = GracefulWorker()
    worker.run()

if __name__ == '__main__':
    main() 