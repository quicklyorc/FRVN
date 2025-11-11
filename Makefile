SHELL := /bin/bash

.PHONY: help dev stop fmt lint build-backend build-frontend deploy-cloudrun deploy-vm

help:
	@echo "Targets:"
	@echo "  dev               - docker compose up (dev)"
	@echo "  stop              - docker compose down"
	@echo "  fmt               - ruff/black & prettier"
	@echo "  lint              - ruff & eslint"
	@echo "  build-backend     - build backend image (prod)"
	@echo "  build-frontend    - build frontend (dist)"
	@echo "  deploy-cloudrun   - deploy to Cloud Run"
	@echo "  deploy-vm         - deploy to VM"

dev:
	docker compose -f docker-compose.dev.yml up -d --build

stop:
	docker compose -f docker-compose.dev.yml down

fmt:
	@echo "Formatting Python with ruff/black (if available)"
	@command -v ruff >/dev/null && ruff format backend || true
	@command -v black >/dev/null && black backend || true
	@echo "Formatting JS/TS with prettier (if available)"
	@command -v npx >/dev/null && (cd frontend && npx prettier --write .) || true

lint:
	@echo "Linting Python with ruff (if available)"
	@command -v ruff >/dev/null && ruff check backend || true
	@echo "Linting JS/TS with eslint (if available)"
	@command -v npx >/dev/null && (cd frontend && npx eslint .) || true

build-backend:
	docker build -t backend:local -f backend/Dockerfile.backend backend

build-frontend:
	cd frontend && npm ci && npm run build

deploy-cloudrun:
	@echo "Using CLI to deploy to Cloud Run..."
	frvn deploy cloudrun --project-root .

deploy-vm:
	@echo "Using CLI to deploy to VM..."
	frvn deploy vm --project-root .


