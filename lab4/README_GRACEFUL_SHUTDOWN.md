# Graceful Shutdown для горизонтально масштабируемого сервиса

## Обзор

Реализована система graceful shutdown для worker'ов, которая обеспечивает:

1. **Уведомление о начале завершения работы** - worker сообщает gateway о начале shutdown
2. **Завершение текущих задач** - worker дожидается завершения обрабатываемой задачи
3. **Корректное закрытие соединений** - Kafka consumer/producer корректно закрываются
4. **Уведомление о завершении** - worker сообщает о полном завершении работы

## Архитектура Graceful Shutdown

### Worker (analyzer.py)
- **Обработка сигналов**: SIGTERM/SIGINT для инициации shutdown
- **Статус уведомления**: отправка статуса через Kafka в топик 'results'
- **Защищенное завершение**: завершение текущей задачи перед shutdown
- **Timeout**: максимум 30 секунд на завершение текущей задачи

### Gateway (app.py)
- **Мониторинг worker'ов**: отслеживание статуса всех worker'ов
- **API endpoints**: `/workers/status` для мониторинга состояния
- **Логирование событий**: важные события shutdown логируются

### Docker
- **stop_grace_period**: 45 секунд для worker'ов, 30 для gateway
- **stop_signal**: SIGTERM для корректной инициации shutdown

## Команды для тестирования

### 1. Запуск системы
```bash
make build
make up
```

### 2. Тестирование graceful shutdown
```bash
# Запуск автоматического теста (в одном терминале)
make test-shutdown

# В другом терминале - команды для тестирования:
make restart-worker    # Graceful restart
make scale-down       # Уменьшение до 1 worker'а
make scale-up         # Увеличение до 3 worker'ов
```

### 3. Мониторинг состояния
```bash
make status   # Статус всех worker'ов
make health   # Общее состояние системы
make logs     # Логи всех сервисов
```

## Статусы Worker'ов

Worker'ы отправляют следующие уведомления:

- **`worker_started`** - worker запущен и готов к работе
- **`shutdown_started`** - получен сигнал завершения, начинается graceful shutdown
- **`shutdown_completed`** - worker полностью завершил работу

## API Endpoints

### GET /workers/status
Возвращает информацию о всех worker'ах:
```json
{
  "total_workers": 2,
  "active_workers": 2,
  "shutting_down_workers": 0,
  "workers": {
    "worker_container_1": {
      "status": "worker_started",
      "current_task": null,
      "last_update": 1703123456,
      "seconds_since_update": 5,
      "is_responsive": true
    }
  }
}
```

### GET /health
Возвращает общее состояние системы:
```json
{
  "status": "ok",
  "kafka_connected": true,
  "producer_ready": true,
  "active_workers": 2
}
```

## Процесс Graceful Shutdown

1. **Получение сигнала** (SIGTERM)
   ```
   🛑 Worker worker_1 received SIGTERM, initiating graceful shutdown...
   ```

2. **Уведомление о начале shutdown**
   ```
   📡 Worker worker_1 sent shutdown_started notification
   ```

3. **Ожидание завершения текущей задачи**
   ```
   ⏳ Worker worker_1 waiting for current task task_123 to complete...
   ```

4. **Закрытие соединений**
   ```
   ✅ Worker worker_1 consumer closed
   ✅ Worker worker_1 producer closed
   ```

5. **Финальное уведомление**
   ```
   📡 Worker worker_1 sent shutdown_completed notification
   👋 Worker worker_1 gracefully shut down
   ```

## Тестовые сценарии

### Сценарий 1: Graceful restart
```bash
# Терминал 1
make test-shutdown

# Терминал 2
make restart-worker
```
**Ожидаемое поведение**: Worker завершает текущую задачу, отправляет уведомления, перезапускается

### Сценарий 2: Масштабирование вниз
```bash
# Терминал 1  
make test-shutdown

# Терминал 2
make scale-down
```
**Ожидаемое поведение**: Лишние worker'ы корректно завершаются, активный worker продолжает обработку

### Сценарий 3: Сравнение с принудительной остановкой
```bash
# Graceful shutdown
docker-compose restart worker

# Принудительная остановка (для сравнения)
docker-compose kill worker
```

## Особенности реализации

- **Thread-safe**: использование Lock для защиты состояния
- **Timeout protection**: максимальное время ожидания завершения задачи
- **Manual commit**: ручное подтверждение обработки сообщений Kafka
- **Monitoring**: реактивное отслеживание состояния через уведомления
- **Resilience**: система продолжает работать при graceful shutdown части worker'ов

## Логи для мониторинга

Важные события логируются с emoji для удобства:
- 🚀 Запуск worker'а
- 🛑 Начало shutdown
- ⏳ Ожидание завершения задачи  
- 🧹 Процесс cleanup
- 👋 Завершение работы
- 📡 Отправка уведомлений 