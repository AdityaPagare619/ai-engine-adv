# JEE Smart AI Platform - Makefile
# Expert Docker and development commands

.PHONY: help clean build up down restart logs test format lint

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "${BLUE}JEE Smart AI Platform - Available Commands${NC}"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# Docker Expert Commands
clean: ## 🧹 Clean Docker system (removes old containers, images, volumes)
	@echo "${YELLOW}🧹 Cleaning Docker system...${NC}"
	@docker container prune -f
	@docker image prune -f
	@docker volume prune -f
	@docker network prune -f
	@echo "${GREEN}✅ Docker system cleaned${NC}"

clean-all: ## 🔥 Nuclear clean - removes everything including unused images
	@echo "${RED}🔥 Nuclear Docker clean - removing everything...${NC}"
	@docker system prune -af --volumes
	@echo "${GREEN}✅ Complete Docker cleanup finished${NC}"

build: ## 🔨 Build all services (with cache optimization)
	@echo "${BLUE}🔨 Building services with cache optimization...${NC}"
	@docker-compose build --parallel
	@echo "${GREEN}✅ All services built successfully${NC}"

build-no-cache: ## 🔨 Build all services without cache
	@echo "${BLUE}🔨 Building services without cache...${NC}"
	@docker-compose build --no-cache --parallel
	@echo "${GREEN}✅ All services built successfully${NC}"

up: ## 🚀 Start all services
	@echo "${BLUE}🚀 Starting all services...${NC}"
	@docker-compose up -d
	@echo "${GREEN}✅ All services started${NC}"
	@make status

up-build: ## 🚀 Build and start all services
	@echo "${BLUE}🚀 Building and starting all services...${NC}"
	@docker-compose up -d --build
	@echo "${GREEN}✅ All services built and started${NC}"
	@make status

down: ## 🛑 Stop all services
	@echo "${YELLOW}🛑 Stopping all services...${NC}"
	@docker-compose down
	@echo "${GREEN}✅ All services stopped${NC}"

down-volumes: ## 🛑 Stop services and remove volumes (DATA LOSS WARNING)
	@echo "${RED}🛑 Stopping services and removing volumes...${NC}"
	@docker-compose down -v
	@echo "${GREEN}✅ Services stopped and volumes removed${NC}"

restart: ## 🔄 Restart all services
	@echo "${BLUE}🔄 Restarting all services...${NC}"
	@docker-compose restart
	@echo "${GREEN}✅ All services restarted${NC}"
	@make status

status: ## 📊 Show service status
	@echo "${BLUE}📊 Service Status:${NC}"
	@docker-compose ps

logs: ## 📋 Show logs for all services
	@echo "${BLUE}📋 Service Logs:${NC}"
	@docker-compose logs -f

logs-admin: ## 📋 Show admin service logs
	@docker-compose logs -f admin-service

logs-db: ## 📋 Show database logs
	@docker-compose logs -f postgres

health: ## 🏥 Check health of all services
	@echo "${BLUE}🏥 Checking service health...${NC}"
	@curl -f http://localhost:8001/health || echo "${RED}❌ Admin service unhealthy${NC}"
	@curl -f http://localhost:8004/health || echo "${RED}❌ Database manager unhealthy${NC}"

# Development Commands
dev: ## 🔧 Start development environment
	@echo "${BLUE}🔧 Starting development environment...${NC}"
	@cp .env.template .env
	@docker-compose -f docker-compose.yml up -d --build
	@make status
	@echo "${GREEN}✅ Development environment ready${NC}"

prod: ## 🏭 Start production environment
	@echo "${BLUE}🏭 Starting production environment...${NC}"
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@make status

# Database Commands
db-shell: ## 🗄️ Connect to database shell
	@docker-compose exec postgres psql -U jee_admin -d jee_smart_platform

db-backup: ## 💾 Backup database
	@echo "${BLUE}💾 Creating database backup...${NC}"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U jee_admin jee_smart_platform > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "${GREEN}✅ Database backup created${NC}"

db-migrate: ## 🗄️ Run database migrations
	@echo "${BLUE}🗄️ Running database migrations...${NC}"
	@docker-compose exec postgres psql -U jee_admin -d jee_smart_platform -f /docker-entrypoint-initdb.d/001_foundation_schema.sql
	@docker-compose exec postgres psql -U jee_admin -d jee_smart_platform -f /docker-entrypoint-initdb.d/initial_data.sql
	@echo "${GREEN}✅ Database migrations completed${NC}"

# Testing Commands
test: ## 🧪 Run tests
	@echo "${BLUE}🧪 Running tests...${NC}"
	@docker-compose exec admin-service python -m pytest tests/ -v
	@echo "${GREEN}✅ Tests completed${NC}"

test-health: ## 🧪 Test all health endpoints
	@echo "${BLUE}🧪 Testing health endpoints...${NC}"
	@curl -s http://localhost:8001/health | jq '.'
	@curl -s http://localhost:8004/health | jq '.'
	@echo "${GREEN}✅ Health tests completed${NC}"

# Code Quality
format: ## ✨ Format code with black
	@echo "${BLUE}✨ Formatting code...${NC}"
	@docker run --rm -v $(PWD):/code pyfound/black:latest black /code --exclude venv
	@echo "${GREEN}✅ Code formatted${NC}"

lint: ## 🔍 Lint code with ruff
	@echo "${BLUE}🔍 Linting code...${NC}"
	@docker run --rm -v $(PWD):/code charliermarsh/ruff:latest check /code
	@echo "${GREEN}✅ Code linting completed${NC}"

# Phase Testing
phase1-test: ## 🎯 Complete Phase 1 testing sequence
	@echo "${BLUE}🎯 Starting Phase 1 complete testing...${NC}"
	@make clean
	@make build
	@make up
	@sleep 10
	@make health
	@make test-admin
	@make test-db-manager
	@echo "${GREEN}✅ Phase 1 testing completed successfully${NC}"

test-admin: ## 🧪 Test admin service
	@echo "${BLUE}🧪 Testing admin service...${NC}"
	@curl -X POST http://localhost:8001/admin/login -H "Content-Type: application/json" -d '{"admin_key": "jee-admin-2025-secure"}' || echo "${RED}❌ Admin login test failed${NC}"

test-db-manager: ## 🧪 Test database manager service
	@echo "${BLUE}🧪 Testing database manager...${NC}"
	@curl -s http://localhost:8004/database/health | jq '.' || echo "${RED}❌ Database manager test failed${NC}"

# Quick Commands
quick-rebuild: clean build up ## 🚀 Quick rebuild everything
	@echo "${GREEN}✅ Quick rebuild completed${NC}"

reset-dev: down-volumes dev ## 🔄 Reset development environment completely
	@echo "${GREEN}✅ Development environment reset${NC}"
