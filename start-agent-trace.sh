#!/bin/bash

# Agent Trace UI 快速启动脚本
#
# 此脚本将自动启动所有需要的服务：
# 1. Qdrant 数据库（Docker）
# 2. 后端 API 服务器
# 3. 前端开发服务器

set -e

echo "================================================"
echo "🚀 SNI Search - Agent Trace UI 启动脚本"
echo "================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
echo -e "${BLUE}[1/3] 检查 Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 正在运行${NC}"
echo ""

# 启动 Qdrant
echo -e "${BLUE}[2/3] 启动 Qdrant 数据库...${NC}"
if docker ps | grep -q qdrant/qdrant; then
    echo -e "${YELLOW}⚠️  Qdrant 已在运行，跳过${NC}"
else
    docker run -d -p 6333:6333 qdrant/qdrant
    echo -e "${GREEN}✅ Qdrant 已启动 (http://localhost:6333)${NC}"
fi
echo ""

# 检查后端依赖
echo -e "${BLUE}[3/3] 检查后端依赖...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，运行 uv sync...${NC}"
    uv sync
fi
echo -e "${GREEN}✅ 后端依赖已就绪${NC}"
echo ""

# 启动后端（后台运行）
echo -e "${BLUE}启动后端 API 服务器...${NC}"
uv run python -m src.api_server > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID, 日志: backend.log)${NC}"
echo ""

# 等待后端启动
echo -e "${YELLOW}等待后端就绪...${NC}"
sleep 3

# 检查后端是否运行
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 后端健康检查通过${NC}"
else
    echo -e "${RED}❌ 后端启动失败，请检查 backend.log${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo ""

# 启动前端（前台运行）
echo -e "${BLUE}启动前端开发服务器...${NC}"
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 所有服务已启动！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "📍 服务地址："
echo -e "   - 前端: ${BLUE}http://localhost:5173${NC}"
echo -e "   - 后端: ${BLUE}http://localhost:8000${NC}"
echo -e "   - Qdrant: ${BLUE}http://localhost:6333/dashboard${NC}"
echo ""
echo -e "📝 后端日志: ${YELLOW}backend.log${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}停止所有服务...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 清理完成${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 启动前端（前台运行）
cd frontend && npm run dev

# 如果前端退出，清理后端
cleanup
