# Docker 部署

本章介绍如何使用 Docker 将整个 RAG 系统打包部署。

---

## 1. Docker 配置

### 1.1 后端 Dockerfile

创建 `backend/Dockerfile`：

```dockerfile
# backend/Dockerfile

# 使用 Python 3.10 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 前端 Dockerfile

创建 `frontend/Dockerfile`：

```dockerfile
# frontend/Dockerfile

# 使用 Node 18 基础镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 使用 nginx 提供静态文件
FROM nginx:alpine

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=0 /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 1.3 Nginx 配置

创建 `frontend/nginx.conf`：

```nginx
# frontend/nginx.conf

server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 1.4 后端 requirements.txt

创建 `backend/requirements.txt`：

```
# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# LangChain
langchain==0.1.4
langchain-community==0.0.17

# 向量数据库
pymilvus==2.3.3

# 图数据库
neo4j==5.19.0

# Embedding
sentence-transformers==2.3.1

# PyTorch
torch==2.1.2
torchvision==0.16.2
torchaudio==2.1.2

# 文档解析
python-docx==1.1.0

# LLM API
requests==2.31.0

# 数据处理
pydantic==2.5.3
python-dotenv==1.0.0
numpy==1.26.3

# 异步处理
aiohttp==3.9.1
```

---

## 2. Docker Compose 配置

### 2.1 创建项目根目录的 docker-compose.yml

在 `~/rag-knowledge-base/` 创建：

```yaml
# docker-compose.yml

version: '3.8'

services:
  # ============ Milvus ============
  milvus-etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - milvus_etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  milvus-minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - milvus_minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.3
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: milvus-etcd:2379
      MINIO_ADDRESS: milvus-minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - milvus-etcd
      - milvus-minio

  # ============ Neo4j ============
  neo4j:
    container_name: neo4j-standalone
    image: neo4j:5.19-community
    environment:
      - NEO4J_AUTH=neo4j/neo4j123456
      - NEO4J_dbms_mode=Community
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"
      - "7687:7687"
    restart: unless-stopped

  # ============ 后端 ============
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rag-backend
    environment:
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
      - MINIMAX_BASE_URL=https://api.minimax.chat/v
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=neo4j123456
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - API_HOST=0.0.0.0
      - API_PORT=8000
    ports:
      - "8000:8000"
    depends_on:
      - milvus
      - neo4j
    restart: unless-stopped

  # ============ 前端 ============
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: rag-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  milvus_etcd_data:
  milvus_minio_data:
  milvus_data:
  neo4j_data:
  neo4j_logs:
```

---

## 3. 一键启动

### 3.1 配置环境变量

```bash
cd ~/rag-knowledge-base

# 创建 .env 文件
cat > .env << EOF
# MiniMax API Key（必须）
MINIMAX_API_KEY=your_api_key_here
EOF
```

### 3.2 构建并启动

```bash
# 构建 Docker 镜像
docker compose build

# 启动所有服务
docker compose up -d
```

### 3.3 查看服务状态

```bash
docker compose ps
```

**预期输出：**
```
NAME                IMAGE                      COMMAND                           SERVICE   CREATED       STATUS
milvus-etcd         quay.io/coreos/etcd:v3.5.5  etcd -advertise-clie...          milvus-etcd   ...   Up
milvus-minio        minio/minio:RELEASE...     minio server /minio_data...       milvus-minio  ...   Up
milvus-standalone   milvusdb/milvus:v2.3.3     milvus run standalone             milvus        ...   Up
neo4j-standalone     neo4j:5.19-community      /startup/docker-entrypoint.       neo4j         ...   Up
rag-backend         rag-backend               uvicorn app.main:app...           backend      ...   Up
rag-frontend        rag-frontend              /docker-entrypoint.d/...          frontend     ...   Up
```

### 3.4 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看指定服务日志
docker compose logs -f backend
```

---

## 4. 访问服务

启动成功后，访问以下地址：

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| FastAPI Docs | http://localhost:8000/docs |
| Milvus Dashboard | http://localhost:9091 |
| Neo4j Browser | http://localhost:7474 |

---

## 5. 停止服务

```bash
# 停止服务（保留数据）
docker compose stop

# 停止并删除容器（保留数据卷）
docker compose down

# 完全清除（包括数据卷）
docker compose down -v
```

---

## 6. 项目完成！

恭喜！RAG 知识库系统已经部署完成 🎉

**系统功能回顾：**
- ✅ 文档上传与解析（支持 Word .docx）
- ✅ 知识图谱构建（Neo4j 存储实体关系）
- ✅ 知识图谱可视化（ECharts 力导向图）
- ✅ 智能问答（双轨检索 + RRF 融合）
- ✅ LLM 生成答案（MiniMax API）

**下一步建议：**
1. 上传一本红楼梦试试效果
2. 探索不同文档类型的关系抽取
3. 调整分块策略和检索参数优化效果
4. 添加更多功能（如文档管理、用户反馈等）

---

## 附录：快速命令参考

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose stop

# 查看日志
docker compose logs -f

# 重启后端（代码修改后）
docker compose restart backend

# 重新构建
docker compose build --no-cache

# 进入后端容器
docker exec -it rag-backend bash

# 进入 Neo4j cypher shell
docker exec -it neo4j-standalone cypher-shell -u neo4j -p neo4j123456
```
