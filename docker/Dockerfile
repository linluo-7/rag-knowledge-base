# 多阶段构建 Dockerfile

# ===== 阶段1: 构建依赖 =====
FROM python:3.10-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装 Python 依赖
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip wheel
RUN pip install --no-cache-dir -r /app/requirements.txt


# ===== 阶段2: 运行镜像 =====
FROM python:3.10-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY backend/app /app/app
COPY backend/.env.example /app/.env.example

# 创建日志目录
RUN mkdir -p /app/logs /app/uploads

# 暴露端口
EXPOSE 5003

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5003"]