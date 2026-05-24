FROM node:18-alpine AS plugin-builder

WORKDIR /app/plugin
COPY adapters/openclaw/plugin/package.json .
RUN npm install --production

# ============================================
# Stage 2: Python runtime
# ============================================
FROM python:3.11-slim

LABEL maintainer="GreyDGW"
LABEL description="Flow Ecosystem - Cognitive Symbiosis Engine for OpenClaw"
LABEL version="7.8-9"

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js (用于 OpenClaw Plugin)
COPY --from=plugin-builder /app/plugin/node_modules ./node_modules

# 安装 OpenClaw CLI
RUN npm install -g openclaw@latest 2>/dev/null || true

WORKDIR /app

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p data logs ~/.openclaw/skills ~/.openclaw/extensions

# 设置环境变量
ENV FLOW_EVOLUTION_DIR=/app
ENV PYTHONPATH=/app
ENV NODE_PATH=/app/node_modules

# 暴露端口 (Gateway)
EXPOSE 18789

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python3 -c "
import sqlite3, os
db_path = os.environ.get('FLOW_EVOLUTION_DIR', '/app') + '/data/flow_ecosystem.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sessions')
    print(f'OK: {c.fetchone()[0]} sessions')
    conn.close()
else:
    print('WAITING: database not yet initialized')
    exit(1)
" || echo "Healthcheck not available"

# 默认命令: 启动全链路
CMD ["bash", "-c", "\
    chmod +x install_v2.sh healthcheck.sh scripts/*.sh && \
    echo '=== Flow Ecosystem Container ===' && \
    bash healthcheck.sh && \
    echo '' && \
    echo 'Starting services...' && \
    bash scripts/start_poll.sh && \
    exec openclaw gateway run --port 18789 \
"]
