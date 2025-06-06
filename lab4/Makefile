.PHONY: build up down logs test scale-up scale-down restart-worker test-shutdown

# Основные команды
build:
	sudo docker-compose build

up:
	sudo docker-compose up -d

down:
	docker-compose down -v

logs:
	docker-compose logs -f

# Тестирование системы
test:
	python3 text_client.py

# Команды для graceful shutdown тестирования
test-shutdown:
	python3 test_graceful_shutdown.py

# Масштабирование
scale-up:
	docker-compose up -d --scale worker=3

scale-down:
	docker-compose up -d --scale worker=1

# Graceful restart одного worker'а
restart-worker:
	docker-compose restart worker

# Принудительная остановка worker'а (для сравнения)
kill-worker:
	docker-compose kill worker

# Мониторинг состояния
status:
	curl -s http://localhost:8080/workers/status | python3 -m json.tool

health:
	curl -s http://localhost:8080/health | python3 -m json.tool 