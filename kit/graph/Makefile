COMPOSE := docker compose -f docker-compose.yml
COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: up down etl import web web-logs web-local web-install api logs reset etl-local import-local

up:
	$(COMPOSE) up -d neo4j

down:
	$(COMPOSE) down

etl:
	$(COMPOSE) run --rm etl python -m etl.run

import:
	$(COMPOSE) run --rm etl python -m etl.import_neo4j

web:
	$(COMPOSE_DEV) --profile web up -d --build web

web-logs:
	$(COMPOSE_DEV) --profile web logs -f web

web-local:
	cd web && npm run dev

web-install:
	cd web && npm install

api:
	$(COMPOSE_DEV) --profile api up -d api

logs:
	$(COMPOSE) logs -f

reset:
	$(COMPOSE) down -v

# 无 Docker 时本地运行（需 pip install -r docker/etl/requirements.txt）
etl-local:
	PYTHONPATH=. python -m etl.run

import-local:
	NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=$${NEO4J_PASSWORD:-graphdb-dev-password} \
		PYTHONPATH=. python -m etl.import_neo4j
