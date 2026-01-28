# Docker 配置
DOCKER_USERNAME ?= lafdrew
VERSION := $(shell git describe --tags --always --dirty)
BACKEND_BASE_IMAGE := $(DOCKER_USERNAME)/sni-backend-base
BACKEND_IMAGE := $(DOCKER_USERNAME)/sni-backend
FRONTEND_IMAGE := $(DOCKER_USERNAME)/sni-frontend

.PHONY: help
help: ## 显示帮助信息
	@echo "SNI Recognition System - Docker 构建命令"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============ 构建命令 ============

.PHONY: build-base-backend
build-base-backend: ## 构建后端 Base 镜像（仅在依赖变化时）
	docker build -f docker/base-backend.Dockerfile -t $(BACKEND_BASE_IMAGE):latest .

.PHONY: build-backend
build-backend: ## 快速构建后端镜像
	docker build -f docker/backend.Dockerfile \
		--build-arg BASE_IMAGE=$(BACKEND_BASE_IMAGE):latest \
		-t $(BACKEND_IMAGE):$(VERSION) \
		-t $(BACKEND_IMAGE):latest .

.PHONY: build-frontend
build-frontend: ## 构建前端镜像
	cd frontend && docker build -f ../docker/frontend.Dockerfile \
		--build-arg VITE_API_BASE_URL=http://localhost:9000 \
		-t $(FRONTEND_IMAGE):$(VERSION) \
		-t $(FRONTEND_IMAGE):latest .

.PHONY: build-all
build-all: build-backend build-frontend ## 构建所有镜像（快速）

.PHONY: build-full
build-full: build-base-backend build-backend build-frontend ## 完整构建（包含 base）

# ============ 推送命令 ============

.PHONY: push-base
push-base: ## 推送 Base 镜像到 Docker Hub
	docker push $(BACKEND_BASE_IMAGE):latest

.PHONY: push-backend
push-backend: ## 推送后端镜像到 Docker Hub
	docker push $(BACKEND_IMAGE):$(VERSION)
	docker push $(BACKEND_IMAGE):latest

.PHONY: push-frontend
push-frontend: ## 推送前端镜像到 Docker Hub
	docker push $(FRONTEND_IMAGE):$(VERSION)
	docker push $(FRONTEND_IMAGE):latest

.PHONY: push-all
push-all: push-backend push-frontend ## 推送所有应用镜像

.PHONY: release
release: build-all push-all ## 构建并发布（完整流程）
	@echo "✓ Released version $(VERSION)"

# ============ 开发命令 ============

.PHONY: dev-up
dev-up: ## 启动开发环境
	docker-compose -f docker-compose.dev.yml up -d

.PHONY: dev-down
dev-down: ## 停止开发环境
	docker-compose -f docker-compose.dev.yml down

.PHONY: dev-logs
dev-logs: ## 查看开发环境日志
	docker-compose -f docker-compose.dev.yml logs -f

.PHONY: dev-restart-backend
dev-restart-backend: ## 重启后端（代码修改后）
	docker-compose -f docker-compose.dev.yml restart backend

.PHONY: dev-rebuild-backend
dev-rebuild-backend: build-backend ## 重新构建并重启后端
	docker-compose -f docker-compose.dev.yml up -d --force-recreate backend

# ============ 生产命令 ============

.PHONY: prod-up
prod-up: ## 启动生产环境（从 Docker Hub 拉取）
	docker-compose up -d

.PHONY: prod-down
prod-down: ## 停止生产环境
	docker-compose down

.PHONY: prod-logs
prod-logs: ## 查看生产环境日志
	docker-compose logs -f

.PHONY: prod-pull
prod-pull: ## 拉取最新镜像
	docker pull $(BACKEND_IMAGE):latest
	docker pull $(FRONTEND_IMAGE):latest
	docker pull qdrant/qdrant:latest

.PHONY: prod-update
prod-update: prod-pull ## 更新并重启服务
	docker-compose up -d --force-recreate

# ============ 工具命令 ============

.PHONY: clean
clean: ## 清理未使用的镜像和容器
	docker system prune -f

.PHONY: clean-all
clean-all: ## 清理所有（包括数据卷）
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -af --volumes

.PHONY: logs
logs: prod-logs ## 查看日志（别名）

.PHONY: status
status: ## 查看容器状态
	docker-compose ps
