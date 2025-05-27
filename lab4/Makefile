.PHONY: build up down scale logs clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

scale:
	docker-compose up -d --scale worker=5

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f 