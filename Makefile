.PHONY: help test lint compile up down logs

help:
	@echo "make test     - run the unittest suite"
	@echo "make lint     - ruff check"
	@echo "make compile  - byte-compile the service, scripts and tests"
	@echo "make up       - build and start the combined app on :8899"
	@echo "make down     - stop the stack"
	@echo "make logs     - follow the service logs"

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

lint:
	ruff check msme tests tools run.py

compile:
	python3 -m compileall -q msme run.py tools tests

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f msme-service
