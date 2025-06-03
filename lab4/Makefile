.PHONY: build run test clean

build:
	docker-compose build

run:
	docker-compose up -d --scale worker=3

test:
	python text_client.py

clean:
	docker-compose down -v 