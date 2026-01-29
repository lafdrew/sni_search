# ============ 构建阶段 ============
FROM node:20-alpine AS builder

WORKDIR /build

# 复制依赖清单
COPY frontend/package*.json ./

# 安装依赖（包含 devDependencies 用于构建）
RUN npm ci

# 复制源代码
COPY frontend/ .

# 构建参数：后端 API 地址
ARG VITE_API_BASE_URL=http://localhost:9000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 构建生产版本
RUN npm run build

# ============ 生产阶段 ============
FROM nginx:alpine

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 复制 Nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 修改文件权限
RUN chown -R nginx:nginx /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
