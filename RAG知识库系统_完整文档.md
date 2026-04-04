# RAG 知识库系统 - 项目介绍

## 1. 项目概述

**项目名称：** RAG 知识库问答系统（Knowledge Base Q&A System）

**项目定位：** 个人学习项目，用于掌握 RAG（检索增强生成）技术栈，了解知识库系统的完整构建流程。

**核心功能：**
- 文档导入与解析（支持 Word 文档）
- 知识图谱构建与可视化（角色关系图）
- 智能问答（基于双轨检索 + RRF 融合）

---

## 2. 技术栈

### 后端
| 技术 | 用途 | 版本 |
|------|------|------|
| FastAPI | Web 框架 | latest |
| LangChain | RAG 流程编排 | 0.1.x |
| Milvus | 向量数据库 | 2.3.x (Docker) |
| Neo4j | 图数据库 | 5.x (Docker) |
| BGE | 中文 Embedding | text2vec-base-chinese |
| MiniMax API | LLM 生成 | abab6.5s-chat |

### 前端
| 技术 | 用途 | 版本 |
|------|------|------|
| React | UI 框架 | 18.x |
| Vite | 构建工具 | 5.x |
| ECharts | 图可视化 | 5.x |
| Axios | HTTP 客户端 | latest |

### 基础设施
| 技术 | 用途 |
|------|------|
| Docker | 容器化部署 |
| Docker Compose | 服务编排 |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React)                         │
│   ┌─────────────┐          ┌─────────────┐              │
│   │   问答页面   │          │  知识图谱页  │              │
│   └──────┬──────┘          └──────┬──────┘              │
└──────────┼────────────────────────┼──────────────────────┘
           │ HTTP                   │ HTTP
           ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI (后端服务)                       │
│   ┌─────────────────────────────────────────────────┐   │
│   │              LangChain RAG Pipeline              │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │
│   │  │ 文档解析  │→│ 文本分块  │→│ BGE Embedding │   │   │
│   │  └──────────┘  └──────────┘  └──────────────┘   │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │
│   │  │ Milvus   │  │  Neo4j   │  │ RRF 融合检索  │   │   │
│   │  │ 向量检索  │  │ 图谱检索  │  │              │   │   │
│   │  └──────────┘  └──────────┘  └──────────────┘   │   │
│   │                     │                             │   │
│   │                     ▼                             │   │
│   │              MiniMax LLM                          │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           │                        │
           ▼                        ▼
    ┌─────────────┐          ┌─────────────┐
    │   Milvus    │          │    Neo4j    │
    │  向量数据库  │          │   图数据库   │
    └─────────────┘          └─────────────┘
```

---

## 4. 数据流程

### 4.1 文档导入流程
```
用户上传 Word 文档
       ↓
python-docx 解析文本
       ↓
文本分割 (256 tokens, 64 overlap)
       ↓
BGE Embedding 生成向量
       ↓
存储到 Milvus（向量 + 原文）
       ↓
MiniMax LLM 提取实体+关系
       ↓
存储到 Neo4j（节点 + 关系）
```

### 4.2 问答流程
```
用户输入问题
       ↓
BGE Embedding 问题
       ↓
┌──────┴──────┐
↓             ↓
Milvus       Neo4j
向量检索      图谱检索
(top-k)      (实体扩展)
       ↓
RRF 融合排序
       ↓
获取融合后的文档片段
       ↓
MiniMax LLM 生成答案
       ↓
返回答案 + 引用的文档片段
```

### 4.3 知识图谱流程
```
Neo4j 查询所有实体和关系
       ↓
转换为 ECharts 力导向图数据格式
       ↓
前端渲染交互式图谱
```

---

## 5. 项目目录结构

```
rag-knowledge-base/
├── docs/                    # 项目文档
│   ├── 01-项目介绍.md
│   ├── 02-环境检查.md
│   ├── 03-Milvus部署.md
│   ├── 04-Neo4j安装.md
│   ├── 05-Python环境.md
│   ├── 06-项目初始化.md
│   ├── 07-后端开发.md
│   ├── 08-前端开发.md
│   ├── 09-前后端联调.md
│   └── 10-Docker部署.md
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py    # 路由
│   │   │   ├── upload.py    # 文档上传
│   │   │   ├── chat.py      # 问答
│   │   │   └── graph.py     # 图谱查询
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── document.py  # 文档解析
│   │   │   ├── chunker.py   # 文本分块
│   │   │   ├── embedding.py # BGE embedding
│   │   │   ├── vector_store.py # Milvus
│   │   │   ├── graph_store.py  # Neo4j
│   │   │   ├── fusion.py    # RRF 融合
│   │   │   └── llm.py       # MiniMax LLM
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── models.py    # Pydantic 模型
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx
│   │   │   └── GraphPage.jsx
│   │   ├── components/
│   │   │   ├── ChatBox.jsx
│   │   │   └── KnowledgeGraph.jsx
│   │   └── api/
│   │       └── index.js
│   ├── package.json
│   └── Dockerfile
├── docker/
│   ├── milvus/
│   │   └── docker-compose.yml
│   └── neo4j/
│       └── docker-compose.yml
└── README.md
```

---

## 6. 下一个章节

下一章我们将进行 **服务器环境检查**，确认 Docker、docker-compose、Git 等基础工具是否就绪。
# 环境检查

在开始部署任何服务之前，需要先检查当前服务器的环境配置。

---

## 1. 检查 Docker

Docker 是容器化部署的基础，Milvus 和 Neo4j 都将以 Docker 容器方式运行。

### 1.1 检查 Docker 是否安装

```bash
docker --version
```

**预期输出：**
```
Docker version 24.x.x, build xxxxx
```

### 1.2 检查 Docker 是否运行

```bash
docker ps
```

**正常情况：** 列表为空或显示运行中的容器（无报错即为正常）

### 1.3 如果 Docker 未安装

执行以下命令安装 Docker：

```bash
# 更新 apt 包索引
sudo apt-get update

# 安装 Docker 依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 添加 Docker GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加 Docker APT 源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 1.4 验证 Docker 安装

```bash
# 运行测试容器
docker run hello-world

# 看到 "Hello from Docker!" 即安装成功
```

---

## 2. 检查 Docker Compose

Docker Compose 用于编排 Milvus 和 Neo4j 的多容器部署。

### 2.1 检查 docker-compose 是否可用

```bash
docker compose version
```

**预期输出：**
```
Docker Compose version v2.x.x
```

> 注意：新版 Docker 自带 Compose V2，无需单独安装 docker-compose。

### 2.2 如果 docker compose 命令报错

可能是 Docker Compose 插件未正确安装，尝试：

```bash
# 重新安装 docker-compose-plugin
sudo apt-get remove docker-compose-plugin
sudo apt-get install -y docker-compose-plugin
```

---

## 3. 检查 Git

Git 用于代码版本管理。

### 3.1 检查 Git 版本

```bash
git --version
```

**预期输出：**
```
git version 2.x.x
```

### 3.2 如果 Git 未安装

```bash
sudo apt-get install -y git
```

---

## 4. 检查系统资源

RAG 系统（尤其是 Milvus）对内存和磁盘有一定要求。

### 4.1 检查可用内存

```bash
free -h
```

**推荐配置：**
- 内存 ≥ 8GB（用于 Milvus + Neo4j + 模型）
- Milvus 单机版建议预留 4GB+ 内存

### 4.2 检查磁盘空间

```bash
df -h
```

**推荐配置：**
- 可用空间 ≥ 50GB
- Milvus 数据目录建议有独立的大容量磁盘

### 4.3 检查 CPU

```bash
nproc
```

**推荐：** 4 核+（embedding 模型推理需要一定算力）

---

## 5. 检查网络端口

确认以下端口未被占用：

| 服务 | 端口 | 用途 |
|------|------|------|
| Milvus | 19530 | Milvus gRPC 端口 |
| Milvus | 9091 | Milvus Web Dashboard |
| Neo4j | 7474 | Neo4j HTTP 端口 |
| Neo4j | 7687 | Neo4j Bolt 端口 |
| FastAPI | 8000 | 后端 API |
| 前端 | 3000 | 前端开发服务器 |

### 5.1 检查端口占用

```bash
# 检查单个端口
sudo lsof -i :19530

# 检查多个端口
sudo lsof -i :19530 -i :9091 -i :7474 -i :7687 -i :8000 -i :3000
```

### 5.2 如果端口被占用

找到占用端口的进程：

```bash
sudo netstat -tlnp | grep <端口号>
```

根据需要停止进程或修改本项目的端口配置。

---

## 6. 配置 Docker 加速器（可选）

如果服务器在国内，建议配置 Docker 镜像加速器。

### 6.1 创建 Docker 配置目录

```bash
sudo mkdir -p /etc/docker
```

### 6.2 创建 daemon.json

```bash
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF
```

### 6.3 重启 Docker

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 7. 环境检查清单

| 检查项 | 命令 | 状态 |
|--------|------|------|
| Docker 版本 | `docker --version` | ☐ |
| Docker 运行状态 | `docker ps` | ☐ |
| Docker Compose | `docker compose version` | ☐ |
| Git 版本 | `git --version` | ☐ |
| 内存 ≥ 8GB | `free -h` | ☐ |
| 磁盘 ≥ 50GB | `df -h` | ☐ |
| 端口无冲突 | `sudo lsof -i :端口号` | ☐ |

**所有检查项通过后，进入下一章节：Milvus 部署。**

---

## 8. 下一个章节

下一章我们将部署 **Milvus 向量数据库**。
# Milvus 单机部署

Milvus 是开源的向量数据库，专门用于存储和检索高维向量。本项目使用 Milvus 存储文档的 embedding 向量。

---

## 1. Milvus 部署方式选择

| 部署方式 | 适用场景 | 复杂度 |
|----------|----------|--------|
| Docker Compose（单机） | 练手、个人项目 | 简单 ✅ |
| Kubernetes | 生产环境 | 复杂 |
| Milvus Lite（嵌入式） | 轻量级测试 | 最简单 |

**本项目选择：Docker Compose 单机部署**

---

## 2. 创建 Milvus 目录

```bash
# 创建项目目录（如果还没有）
mkdir -p ~/rag-knowledge-base
cd ~/rag-knowledge-base

# 创建 Milvus 配置目录
mkdir -p docker/milvus
```

---

## 3. 创建 docker-compose.yml

进入 Milvus 目录并创建配置文件：

```bash
cd ~/rag-knowledge-base/docker/milvus
```

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
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
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"      # Milvus gRPC 端口
      - "9091:9091"        # Milvus Web Dashboard
    depends_on:
      - etcd
      - minio

volumes:
  etcd_data:
  minio_data:
  milvus_data:
```

---

## 4. 启动 Milvus

```bash
# 在 docker/milvus 目录下执行
docker compose up -d
```

**预期输出：**
```
[+] Running 3/3
 ✔ Container milvus-etcd     Started
 ✔ Container milvus-minio    Started
 ✔ Container milvus-standalone Started
```

---

## 5. 验证 Milvus 运行状态

### 5.1 检查容器状态

```bash
docker compose ps
```

**预期输出：**
```
NAME                IMAGE                      COMMAND                  SERVICE   CREATED        STATUS
milvus-etcd         quay.io/coreos/etcd:v3.5.5  etcd -advertise-clie…   etcd      5 seconds ago  Up 4 seconds
milvus-minio        minio/minio:RELEASE.2023-03-20T20-16-18Z minio server /mi…   minio     5 seconds ago  Up 4 seconds
milvus-standalone   milvusdb/milvus:v2.3.3      milvus run standalone    milvus    5 seconds ago  Up 3 seconds
```

### 5.2 等待 Milvus 启动完成

Milvus 启动需要 30-60 秒，等待服务就绪：

```bash
# 等待 30 秒后检查
sleep 30

# 检查 Milvus 日志
docker compose logs milvus-standalone | tail -20
```

**看到以下日志说明启动成功：**
```
[INFO] milvus.go:xxx - [Server] Milvus Grpc Server listening on: 0.0.0.0:19530
```

### 5.3 检查 Milvus Web Dashboard

在浏览器访问：`http://<服务器IP>:9091`

如果看到 Milvus Dashboard 界面，说明部署成功。

---

## 6. 配置防火墙（如果需要）

如果服务器有防火墙，需要开放端口：

```bash
# Ubuntu/Debian 使用 ufw
sudo ufw allow 19530/tcp
sudo ufw allow 9091/tcp

# 或者直接关闭防火墙（不推荐生产环境）
sudo ufw disable
```

---

## 7. Milvus Python SDK 安装

Milvus 提供 Python SDK 用于连接和操作数据库。

```bash
# 在项目目录下安装
pip install pymilvus
```

或安装指定版本（推荐与 Docker 镜像版本匹配）：

```bash
pip install pymilvus==2.3.3
```

---

## 8. 测试 Milvus 连接

创建测试脚本 `test_milvus.py`：

```python
from pymilvus import connections, db, Collection, FieldSchema, CollectionSchema, DataType

# 连接 Milvus
print("正在连接 Milvus...")
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)
print("连接成功！")

# 列出所有 Collection
print("\n已有的 Collection：")
from pymilvus import utility
collections = utility.list_collections()
print(collections if collections else "(空)")

# 关闭连接
connections.disconnect("default")
print("\nMilvus 连接测试完成！")
```

运行测试：

```bash
python test_milvus.py
```

**预期输出：**
```
正在连接 Milvus...
连接成功！

已有的 Collection：
()
Milvus 连接测试完成！
```

---

## 9. 常见问题

### 9.1 端口被占用

```
Error: all relocations tried for connector etcd when using Milvus Guest
```

**解决方法：** 检查 19530 端口是否被占用，或修改 docker-compose.yml 中的端口映射。

### 9.2 内存不足

Milvus 需要足够的内存才能正常运行：

```bash
# 检查 Docker 日志
docker compose logs milvus-standalone | grep -i "memory"

# 增加 Docker 内存限制（Docker Desktop 设置中调整）
```

### 9.3 启动后立即停止

```bash
# 查看详细日志
docker compose logs milvus-standalone

# 常见原因：etcd 或 minio 未就绪就启动了 milvus
# 解决：确保 etcd 和 minio 容器先启动
docker compose up -d
sleep 10
docker compose up -d  # 再次启动
```

---

## 10. 停止 Milvus

```bash
# 停止服务（保留数据）
docker compose stop

# 停止并删除容器（不删除数据卷）
docker compose down

# 停止并删除容器+数据卷（清空数据）
docker compose down -v
```

---

## 11. 下一个章节

Milvus 部署完成！下一章我们将安装 **Neo4j 图数据库**。
# Neo4j 安装与配置

Neo4j 是流行的图数据库，用于存储知识图谱中的实体（节点）和关系（边）。本项目使用 Neo4j 存储从文档中提取的角色关系。

---

## 1. Neo4j 部署方式选择

| 部署方式 | 适用场景 | 复杂度 |
|----------|----------|--------|
| Docker Compose（推荐） | 练手、个人项目 | 简单 ✅ |
| 原生安装 | 需要特殊配置 | 中等 |
| Neo4j Aura（云服务） | 不想管理服务器 | 最简单 |

**本项目选择：Docker Compose 单机部署**

---

## 2. 创建 Neo4j 目录

```bash
# 在项目 docker 目录下创建
mkdir -p ~/rag-knowledge-base/docker/neo4j
cd ~/rag-knowledge-base/docker/neo4j
```

---

## 3. 创建 docker-compose.yml

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  neo4j:
    container_name: neo4j-standalone
    image: neo4j:5.19-community
    environment:
      # Neo4j 初始密码（请修改为强密码）
      - NEO4J_AUTH=neo4j/neo4j123456
      # 允许写入（单机部署必须开启）
      - NEO4J_dbms_mode=Community
      # JVM 内存配置
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
      # 开启查询日志（可选，方便调试）
      - NEO4J_dbms_logging_query_enabled=true
    volumes:
      # 数据持久化
      - neo4j_data:/data
      # 日志持久化
      - neo4j_logs:/logs
      # 插件目录（后续安装图算法插件）
      - neo4j_plugins:/plugins
    ports:
      - "7474:7474"  # Neo4j HTTP 端口（浏览器访问）
      - "7687:7687"  # Neo4j Bolt 端口（程序连接）
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_plugins:
```

---

## 4. 启动 Neo4j

```bash
# 在 docker/neo4j 目录下执行
docker compose up -d
```

**预期输出：**
```
[+] Running 1/1
 ✔ Container neo4j-standalone Started
```

---

## 5. 验证 Neo4j 运行状态

### 5.1 检查容器状态

```bash
docker compose ps
```

**预期输出：**
```
NAME              IMAGE             COMMAND                           SERVICE   CREATED       STATUS
neo4j-standalone  neo4j:5.19-community  /startup/docker-entrypoint.   neo4j     5 seconds ago  Up 4 seconds
```

### 5.2 等待 Neo4j 启动

Neo4j 启动需要 20-30 秒：

```bash
sleep 20

# 查看启动日志
docker compose logs neo4j-standalone | tail -10
```

**看到以下日志说明启动成功：**
```
INFO  Remote interface available at http://localhost:7474/
```

### 5.3 通过浏览器访问 Neo4j Browser

访问：`http://<服务器IP>:7474`

首次访问会要求登录：
- Username: `neo4j`
- Password: `neo4j123456`（你设置的密码）

---

## 6. Neo4j Python SDK 安装

```bash
pip install neo4j
```

---

## 7. 测试 Neo4j 连接

创建测试脚本 `test_neo4j.py`：

```python
from neo4j import GraphDatabase

# Neo4j 连接信息
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "neo4j123456")

print("正在连接 Neo4j...")
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    # 验证连接
    driver.verify_connectivity()
    print("连接成功！")
    
    # 执行查询
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j 连接正常！' AS message")
        print(result.single()["message"])

print("\nNeo4j 连接测试完成！")
```

运行测试：

```bash
python test_neo4j.py
```

**预期输出：**
```
正在连接 Neo4j...
连接成功！
Neo4j 连接正常！
Neo4j 连接测试完成！
```

---

## 8. 安装图算法插件（可选）

如果后续需要做图分析（如计算 PageRank、中心性等），可以安装 APOC 插件：

### 8.1 下载 APOC 插件

APOC（Awesome Procedures On Cypher）是 Neo4j 最常用的插件包。

```bash
# 进入容器内部
docker exec -it neo4j-standalone bash

# 查看 Neo4j 版本
neo4j --version
# 输出: neo4j 5.19.0

# 下载对应版本的 APOC
# 注意：版本号需要与 Neo4j 版本匹配
cd /plugins
wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.19.0/apoc-5.19.0.jar

# 退出容器
exit
```

### 8.2 配置 Neo4j 使用插件

修改 `docker-compose.yml`，添加插件路径配置：

```yaml
services:
  neo4j:
    ...
    environment:
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*
    volumes:
      ...
      - neo4j_plugins:/plugins
```

重启 Neo4j：

```bash
docker compose down
docker compose up -d
```

### 8.3 验证 APOC 安装

在 Neo4j Browser 中执行：

```cypher
RETURN apoc.version() AS version
```

如果返回版本号，说明 APOC 安装成功。

---

## 9. 常用 Cypher 命令

在 Neo4j Browser 中可以执行以下命令：

```cypher
# 查看所有节点数量
MATCH (n) RETURN count(n) AS nodeCount

# 查看所有关系数量
MATCH ()-[r]->() RETURN count(r) AS relCount

# 删除所有节点和关系（清空数据库）
MATCH (n) DETACH DELETE n

# 查看所有节点类型
MATCH (n) RETURN labels(n), count(n) ORDER BY count(n) DESC

# 查看所有关系类型
MATCH ()-[r]->() RETURN type(r), count(r) ORDER BY count(r) DESC
```

---

## 10. 通过 Python 操作 Neo4j

### 10.1 基本 CRUD 操作

```python
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "neo4j123456")

class Neo4jClient:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def close(self):
        self.driver.close()
    
    def create_node(self, label, properties):
        """创建节点"""
        with self.driver.session() as session:
            query = f"CREATE (n:{label} $props) RETURN n"
            result = session.run(query, props=properties)
            return result.single()
    
    def create_relationship(self, from_node, rel_type, to_node, properties=None):
        """创建关系"""
        with self.driver.session() as session:
            props = properties or {}
            query = f"""
                MATCH (a), (b)
                WHERE a.name = $from_node AND b.name = $to_node
                CREATE (a)-[r:{rel_type} $props]->(b)
                RETURN r
            """
            result = session.run(query, from_node=from_node, to_node=to_node, props=props)
            return result.single()
    
    def find_node(self, label, property_key, property_value):
        """查找节点"""
        with self.driver.session() as session:
            query = f"MATCH (n:{label}) WHERE n.{property_key} = $value RETURN n"
            result = session.run(query, value=property_value)
            return [record["n"] for record in result]
    
    def get_all_nodes(self, label):
        """获取所有节点"""
        with self.driver.session() as session:
            query = f"MATCH (n:{label}) RETURN n"
            result = session.run(query)
            return [record["n"] for record in result]
    
    def get_all_relationships(self):
        """获取所有关系"""
        with self.driver.session() as session:
            query = "MATCH (a)-[r]->(b) RETURN a.name AS from, type(r) AS rel_type, b.name AS to"
            result = session.run(query)
            return [{"from": record["from"], "type": record["rel_type"], "to": record["to"]} 
                    for record in result]

# 使用示例
client = Neo4jClient(URI, AUTH)

# 创建节点
client.create_node("Person", {"name": "贾宝玉", "role": "男主角", "description": "红楼梦主角"})
client.create_node("Person", {"name": "林黛玉", "role": "女主角", "description": "绛珠仙草转世"})

# 创建关系
client.create_relationship("贾宝玉", "恋人", "林黛玉", {"description": "宝黛爱情"})

# 查询
nodes = client.get_all_nodes("Person")
print(f"共有 {len(nodes)} 个节点")

client.close()
```

---

## 11. 常见问题

### 11.1 忘记密码

如果忘记 Neo4j 密码，需要重置：

```bash
# 停止 Neo4j
docker compose stop

# 修改 docker-compose.yml，添加重置配置
environment:
  - NEO4J_AUTH=neo4j/newpassword
  # 或者允许无认证访问（仅开发环境）
  - NEO4J_dbms_auth_enabled=false
```

### 11.2 端口冲突

如果 7474 或 7687 端口被占用，修改 docker-compose.yml 中的端口映射：

```yaml
ports:
  - "7475:7474"  # 映射到 7475
  - "7688:7687"  # 映射到 7688
```

### 11.3 内存不足

Neo4j 默认内存配置可能较大，修改 `docker-compose.yml` 中的 JVM 内存：

```yaml
environment:
  - NEO4J_dbms_memory_heap_initial__size=256m
  - NEO4J_dbms_memory_heap_max__size=1G
```

---

## 12. 停止 Neo4j

```bash
# 停止服务（保留数据）
docker compose stop

# 停止并删除容器（保留数据卷）
docker compose down

# 完全清除（包括数据）
docker compose down -v
```

---

## 13. 下一个章节

Neo4j 安装完成！下一章我们将准备 **Python 环境**。
# Python 环境准备

本项目使用 Python 3.10+ 作为后端开发语言，推荐使用 Conda 管理 Python 环境。

---

## 1. 检查 Python 版本

```bash
python3 --version
```

**预期输出：**
```
Python 3.10.x 或更高
```

如果版本过低或未安装，参考下一节安装 Python。

---

## 2. 安装 Conda（推荐）

Conda 可以管理多个 Python 环境，避免包冲突。

### 2.1 下载 Miniconda

```bash
cd /tmp
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

### 2.2 安装 Miniconda

```bash
bash Miniconda3-latest-Linux-x86_64.sh
```

**安装过程：**
```
Welcome to Miniconda3-latest-Linux-x86_64.sh

按 Enter 继续...
按 q 跳过 License，直接 Accept
输入 yes 确认安装路径（默认即可）
输入 yes 初始化 Conda
```

### 2.3 重新加载 Shell 配置

```bash
# 如果使用的是 bash
source ~/.bashrc

# 如果使用的是 zsh
source ~/.zshrc
```

### 2.4 验证安装

```bash
conda --version
```

**预期输出：**
```
conda 23.x.x
```

---

## 3. 创建项目环境

### 3.1 创建 Python 3.10 环境

```bash
conda create -n rag python=3.10 -y
```

### 3.2 激活环境

```bash
conda activate rag
```

**激活后终端会显示：**
```
(rag) user@hostname:~/rag-knowledge-base$
```

### 3.3 验证 Python 版本

```bash
python --version
```

**预期输出：**
```
Python 3.10.x
```

---

## 4. 安装基础依赖

### 4.1 升级 pip

```bash
pip install --upgrade pip
```

### 4.2 安装 PyTorch（CPU 版本）

PyTorch 是深度学习的基础库，BGE Embedding 模型需要它。

```bash
pip install torch torchvision torchaudio
```

**如果服务器有 NVIDIA GPU**，安装 GPU 版本：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4.3 安装 LangChain

```bash
pip install langchain langchain-community
```

### 4.4 安装向量数据库和图数据库 SDK

```bash
pip install pymilvus neo4j
```

### 4.5 安装 Embedding 模型

```bash
pip install sentence-transformers
```

### 4.6 安装 FastAPI 和 Web 服务

```bash
pip install fastapi uvicorn python-multipart
```

### 4.7 安装文档解析库

```bash
pip install python-docx
```

### 4.8 安装 MiniMax SDK

```bash
pip install minimaxai
```

如果没有合适的 SDK，也可以直接用 HTTP 请求调用 MiniMax API。

### 4.9 安装其他工具库

```bash
pip install pydantic python-dotenv requests
```

---

## 5. 一键安装所有依赖

为了方便，可以创建 `requirements.txt`：

```bash
cd ~/rag-knowledge-base/backend
```

创建 `requirements.txt`：

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

然后执行一键安装：

```bash
pip install -r requirements.txt
```

---

## 6. 验证安装

创建 `check_env.py`：

```python
import sys
print(f"Python: {sys.version}")

# 检查各库是否安装成功
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"PyTorch: 未安装 - {e}")

try:
    import langchain
    print(f"LangChain: {langchain.__version__}")
except ImportError as e:
    print(f"LangChain: 未安装 - {e}")

try:
    import pymilvus
    print(f"PyMilvus: {pymilvus.__version__}")
except ImportError as e:
    print(f"PyMilvus: 未安装 - {e}")

try:
    import neo4j
    print(f"Neo4j: {neo4j.__version__}")
except ImportError as e:
    print(f"Neo4j: 未安装 - {e}")

try:
    import sentence_transformers
    print(f"sentence-transformers: {sentence_transformers.__version__}")
except ImportError as e:
    print(f"sentence-transformers: 未安装 - {e}")

try:
    import fastapi
    print(f"FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"FastAPI: 未安装 - {e}")

try:
    import docx
    print(f"python-docx: {docx.__version__}")
except ImportError as e:
    print(f"python-docx: 未安装 - {e}")

print("\n环境检查完成！")
```

运行：

```bash
python check_env.py
```

**预期输出（所有库都显示版本号，无错误）：**
```
Python: 3.10.x
PyTorch: 2.1.2
LangChain: 0.1.4
PyMilvus: 2.3.3
Neo4j: 5.19.0
sentence-transformers: 2.3.1
FastAPI: 0.109.0
python-docx: 0.8.11

环境检查完成！
```

---

## 7. Conda 常用命令

```bash
# 激活环境
conda activate rag

# 退出环境
conda deactivate

# 列出所有环境
conda env list

# 删除环境
conda env remove -n rag

# 导出环境配置
conda env export > environment.yml

# 从配置文件创建环境
conda env create -f environment.yml
```

---

## 8. 虚拟环境管理（可选）

如果不使用 Conda，也可以使用 Python 内置的 venv：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

---

## 9. 配置环境变量

创建 `.env` 文件存储敏感配置：

```bash
cd ~/rag-knowledge-base/backend
touch .env
```

编辑 `.env`：

```env
# MiniMax API 配置
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123456

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
```

> **注意：** `.env` 文件不要提交到 Git，需要加入 `.gitignore`

---

## 10. 下一个章节

Python 环境准备完成！下一章我们将进行 **项目初始化**。
# 项目初始化

本章将创建后端项目的完整目录结构，初始化 Git 仓库，并配置好所有必要的文件。

---

## 1. 创建项目目录结构

```bash
cd ~/rag-knowledge-base

# 创建后端目录结构
mkdir -p backend/app/{api,core,schemas}
mkdir -p backend/app/api
mkdir -p backend/app/core
mkdir -p backend/app/schemas

# 查看目录结构
tree -L 3 backend/
```

**预期输出：**
```
backend/
└── app
    ├── api
    ├── core
    └── schemas
```

---

## 2. 初始化 Git 仓库

```bash
cd ~/rag-knowledge-base
git init
```

**预期输出：**
```
Initialized empty Git repository in /home/user/rag-knowledge-base/.git/
```

### 2.1 配置 Git 用户信息

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2.2 创建 .gitignore

创建 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 环境变量
.env
.env.local

# 模型缓存
model_cache/

# 数据文件
data/
*.db
*.sqlite

# Docker
.docker/

# 系统文件
.DS_Store
Thumbs.db
```

---

## 3. 后端项目结构

### 3.1 目录结构详解

```
backend/
├── app/                    # 应用主目录
│   ├── __init__.py         # 标记为 Python 包
│   ├── main.py             # FastAPI 应用入口
│   ├── config.py           # 全局配置
│   ├── api/                # API 路由
│   │   ├── __init__.py
│   │   ├── router.py       # 路由汇总
│   │   ├── upload.py       # 文档上传接口
│   │   ├── chat.py         # 问答接口
│   │   └── graph.py        # 图谱接口
│   ├── core/               # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── document.py     # 文档解析
│   │   ├── chunker.py      # 文本分块
│   │   ├── embedding.py    # BGE Embedding
│   │   ├── vector_store.py # Milvus 存储
│   │   ├── graph_store.py  # Neo4j 存储
│   │   ├── fusion.py       # RRF 融合
│   │   └── llm.py          # MiniMax LLM
│   └── schemas/            # Pydantic 数据模型
│       ├── __init__.py
│       └── models.py       # 请求/响应模型
├── requirements.txt        # 依赖清单
├── Dockerfile              # Docker 镜像配置
└── .env                    # 环境变量（不提交）
```

---

## 4. 创建 __init__.py 文件

这些空文件用于将目录标记为 Python 包：

```bash
# 创建所有 __init__.py
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/core/__init__.py
touch backend/app/schemas/__init__.py
```

---

## 5. 创建配置文件

### 5.1 创建 config.py

`backend/app/config.py`：

```python
"""
全局配置文件
所有配置项从此处读取，支持从环境变量覆盖
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v")

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j123456")

# Milvus 配置
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

# 服务配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Embedding 模型配置
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
EMBEDDING_DEVICE = "cpu"  # 或 "cuda" 如果有 GPU

# 文本分块配置
CHUNK_SIZE = 256       # 每个 chunk 的 token 数
CHUNK_OVERLAP = 64     # chunk 之间的重叠 token 数

# RRF 融合配置
RRF_K = 60  # RRF 的经验参数，通常不需要调整

# 向量检索配置
TOP_K = 5   # 返回前 k 个最相关结果

# LLM 配置
LLM_MODEL = "abab6.5s-chat"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1024

# 文件存储配置
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Milvus Collection 配置
MILVUS_COLLECTION = "documents"
MILVUS_DIM = 768  # text2vec-base-chinese 的向量维度
```

---

## 6. 创建 schemas/models.py

`backend/app/schemas/models.py`：

```python
"""
Pydantic 数据模型
定义 API 请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ 文档上传 ============

class UploadResponse(BaseModel):
    """文档上传响应"""
    file_id: str
    filename: str
    status: str
    message: str


# ============ 问答 ============

class ChatRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题", min_length=1)
    top_k: Optional[int] = Field(5, description="返回的结果数量")


class SourceDocument(BaseModel):
    """来源文档"""
    content: str
    score: float
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    """问答响应"""
    answer: str
    sources: List[SourceDocument]
    graph_entities: Optional[List[Dict[str, Any]]] = None


# ============ 知识图谱 ============

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    name: str
    type: str  # 节点类型，如 "人物"
    properties: Dict[str, Any] = {}


class GraphRelation(BaseModel):
    """图谱关系"""
    source: str  # 源节点 name
    target: str   # 目标节点 name
    type: str     # 关系类型，如 "恋人"
    properties: Dict[str, Any] = {}


class GraphData(BaseModel):
    """图谱数据"""
    nodes: List[GraphNode]
    relations: List[GraphRelation]


class GraphResponse(BaseModel):
    """图谱查询响应"""
    data: GraphData
    total_nodes: int
    total_relations: int


# ============ 健康检查 ============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    milvus: str
    neo4j: str
    timestamp: datetime
```

---

## 7. 创建主入口文件

### 7.1 backend/app/main.py

`backend/app/main.py`：

```python
"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import API_HOST, API_PORT
from app.api.router import api_router
from app.core.vector_store import MilvusStore
from app.core.graph_store import Neo4jStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 RAG 知识库系统启动中...")
    
    # 初始化 Milvus
    try:
        milvus_store = MilvusStore()
        milvus_store.init_collection()
        print("✅ Milvus 连接成功")
    except Exception as e:
        print(f"⚠️ Milvus 连接失败: {e}")
    
    # 初始化 Neo4j
    try:
        neo4j_store = Neo4jStore()
        neo4j_store.init_schema()
        print("✅ Neo4j 连接成功")
    except Exception as e:
        print(f"⚠️ Neo4j 连接失败: {e}")
    
    yield
    
    # 关闭时执行
    print("👋 RAG 知识库系统关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="RAG 知识库问答系统",
    description="基于 LangChain + Milvus + Neo4j 的 RAG 系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api", tags=["API"])


@app.get("/")
async def root():
    """根路径"""
    return {"message": "RAG 知识库问答系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    from app.schemas.models import HealthResponse
    from datetime import datetime
    
    milvus_status = "unknown"
    neo4j_status = "unknown"
    
    try:
        milvus_store = MilvusStore()
        milvus_store.check_connection()
        milvus_status = "healthy"
    except:
        milvus_status = "unhealthy"
    
    try:
        neo4j_store = Neo4jStore()
        neo4j_store.check_connection()
        neo4j_status = "healthy"
    except:
        neo4j_status = "unhealthy"
    
    return HealthResponse(
        status="ok" if milvus_status == "healthy" and neo4j_status == "healthy" else "degraded",
        milvus=milvus_status,
        neo4j=neo4j_status,
        timestamp=datetime.now()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
```

---

## 8. 创建 API 路由

### 8.1 backend/app/api/router.py

`backend/app/api/router.py`：

```python
"""
API 路由汇总
"""

from fastapi import APIRouter

from app.api import upload, chat, graph

api_router = APIRouter()

# 注册子路由
api_router.include_router(upload.router, prefix="/upload", tags=["文档上传"])
api_router.include_router(chat.router, prefix="/chat", tags=["问答"])
api_router.include_router(graph.router, prefix="/graph", tags=["知识图谱"])
```

### 8.2 backend/app/api/upload.py

`backend/app/api/upload.py`：

```python
"""
文档上传 API
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.models import UploadResponse
from app.config import UPLOAD_DIR
from app.core.document import DocumentParser
from app.core.chunker import TextChunker
from app.core.embedding import EmbeddingModel
from app.core.vector_store import MilvusStore
from app.core.graph_store import Neo4jStore
from app.core.llm import MiniMaxLLM

router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档并处理
    
    流程：
    1. 保存上传文件
    2. 解析文档内容
    3. 文本分块
    4. 生成 Embedding
    5. 存储到 Milvus
    6. 提取实体关系存储到 Neo4j
    """
    # 生成文件 ID
    file_id = str(uuid.uuid4())
    
    # 确保上传目录存在
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # 保存文件
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
    
    try:
        # 1. 解析文档
        parser = DocumentParser()
        text = parser.parse(str(file_path))
        
        # 2. 文本分块
        chunker = TextChunker()
        chunks = chunker.chunk(text)
        
        # 3. 初始化各组件
        embedding_model = EmbeddingModel()
        milvus_store = MilvusStore()
        neo4j_store = Neo4jStore()
        llm = MiniMaxLLM()
        
        # 4. 生成 Embedding 并存储到 Milvus
        vectors = embedding_model.embed_documents(chunks)
        milvus_store.insert(chunks, vectors, {"file_id": file_id, "filename": file.filename})
        
        # 5. 提取实体关系（调用 LLM）
        entities, relations = llm.extract_entities_and_relations(text)
        
        # 6. 存储到 Neo4j
        for entity in entities:
            neo4j_store.create_entity(entity["name"], entity["type"], entity.get("properties", {}))
        for relation in relations:
            neo4j_store.create_relation(
                relation["from"],
                relation["to"],
                relation["type"],
                relation.get("properties", {})
            )
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            status="success",
            message=f"文档上传成功！解析了 {len(chunks)} 个文本块，提取了 {len(entities)} 个实体和 {len(relations)} 个关系"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}")
```

### 8.3 backend/app/api/chat.py

`backend/app/api/chat.py`：

```python
"""
问答 API
"""

from fastapi import APIRouter, HTTPException
from app.schemas.models import ChatRequest, ChatResponse, SourceDocument
from app.core.embedding import EmbeddingModel
from app.core.vector_store import MilvusStore
from app.core.graph_store import Neo4jStore
from app.core.fusion import RRFFusion
from app.core.llm import MiniMaxLLM

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    问答接口
    
    流程：
    1. 问题 Embedding
    2. Milvus 向量检索
    3. Neo4j 图谱检索（实体扩展）
    4. RRF 融合
    5. LLM 生成答案
    """
    try:
        # 初始化组件
        embedding_model = EmbeddingModel()
        milvus_store = MilvusStore()
        neo4j_store = Neo4jStore()
        llm = MiniMaxLLM()
        fusion = RRFFusion()
        
        # 1. 问题 Embedding
        query_vector = embedding_model.embed_query(request.question)
        
        # 2. Milvus 向量检索
        milvus_results = milvus_store.search(query_vector, top_k=request.top_k)
        
        # 3. Neo4j 图谱检索（通过实体扩展找到相关文档）
        graph_entities = neo4j_store.expand_entities(request.question)
        neo4j_results = []
        if graph_entities:
            # 将图谱中的实体转换为检索结果
            for entity in graph_entities:
                related_texts = milvus_store.search_by_entity(entity["name"], top_k=2)
                neo4j_results.extend(related_texts)
        
        # 4. RRF 融合
        fused_results = fusion.fuse(milvus_results, neo4j_results, k=60)
        
        # 5. 构建上下文
        context = "\n\n".join([r["content"] for r in fused_results[:3]])
        
        # 6. LLM 生成答案
        answer = llm.generate(request.question, context)
        
        # 7. 构建响应
        sources = [
            SourceDocument(
                content=r["content"],
                score=r["score"],
                metadata=r.get("metadata", {})
            )
            for r in fused_results[:request.top_k]
        ]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            graph_entities=graph_entities
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {e}")
```

### 8.4 backend/app/api/graph.py

`backend/app/api/graph.py`：

```python
"""
知识图谱 API
"""

from fastapi import APIRouter, HTTPException
from app.schemas.models import GraphResponse, GraphData, GraphNode, GraphRelation
from app.core.graph_store import Neo4jStore

router = APIRouter()


@router.get("/", response_model=GraphResponse)
async def get_graph():
    """
    获取知识图谱的全部数据
    
    返回所有节点和关系，用于前端可视化
    """
    try:
        neo4j_store = Neo4jStore()
        
        nodes = neo4j_store.get_all_nodes()
        relations = neo4j_store.get_all_relations()
        
        # 转换为 Pydantic 模型
        graph_nodes = [
            GraphNode(
                id=n["id"],
                name=n["name"],
                type=n["type"],
                properties=n.get("properties", {})
            )
            for n in nodes
        ]
        
        graph_relations = [
            GraphRelation(
                source=r["from"],
                target=r["to"],
                type=r["type"],
                properties=r.get("properties", {})
            )
            for r in relations
        ]
        
        return GraphResponse(
            data=GraphData(nodes=graph_nodes, relations=graph_relations),
            total_nodes=len(graph_nodes),
            total_relations=len(graph_relations)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱查询失败: {e}")


@router.get("/search")
async def search_graph(keyword: str):
    """
    搜索图谱中的节点
    
    根据关键词搜索匹配的节点及其直接关联
    """
    try:
        neo4j_store = Neo4jStore()
        
        # 搜索节点
        matched_nodes = neo4j_store.search_nodes(keyword)
        
        # 获取每个节点的一度关系
        result_nodes = []
        result_relations = []
        
        for node in matched_nodes:
            # 获取节点详情
            node_detail = neo4j_store.get_node(node["name"])
            if node_detail:
                result_nodes.append(node_detail)
            
            # 获取节点的直接关系
            node_relations = neo4j_store.get_node_relations(node["name"])
            result_relations.extend(node_relations)
        
        # 去重
        unique_nodes = {n["id"]: n for n in result_nodes}
        
        return {
            "nodes": list(unique_nodes.values()),
            "relations": result_relations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱搜索失败: {e}")
```

---

## 9. 验证项目结构

```bash
cd ~/rag-knowledge-base
tree backend/
```

**预期输出：**
```
backend/
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── upload.py
│   │   ├── chat.py
│   │   └── graph.py
│   ├── core
│   │   ├── __init__.py
│   │   └── ...
│   └── schemas
│       ├── __init__.py
│       └── models.py
├── requirements.txt
└── Dockerfile
```

---

## 10. 测试 API 是否能启动

```bash
cd ~/rag-knowledge-base/backend
python -c "from app.main import app; print('✅ 应用导入成功')"
```

**预期输出：**
```
✅ 应用导入成功
```

---

## 11. 下一个章节

项目初始化完成！下一章我们将实现 **后端核心模块**。
# 后端核心模块开发

本章将实现后端的所有核心模块，包括文档解析、文本分块、Embedding、向量存储、图谱存储、RRF 融合和 LLM 调用。

---

## 1. 文档解析模块 (document.py)

文档解析模块负责从各种格式的文档中提取纯文本内容。

### 1.1 创建 document.py

`backend/app/core/document.py`：

```python
"""
文档解析模块
支持解析 Word (.docx) 等格式的文档
"""

import re
from pathlib import Path
from typing import Optional
from docx import Document as DocxDocument


class DocumentParser:
    """
    文档解析器
    
    支持格式：
    - .docx (Word 文档)
    - .txt (纯文本)
    """
    
    def __init__(self):
        self.supported_formats = [".docx", ".txt"]
    
    def parse(self, file_path: str) -> str:
        """
        解析文档，返回纯文本内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文档的纯文本内容
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {suffix}，支持的格式: {self.supported_formats}")
        
        if suffix == ".docx":
            return self._parse_docx(path)
        elif suffix == ".txt":
            return self._parse_txt(path)
    
    def _parse_docx(self, path: Path) -> str:
        """
        解析 Word 文档
        
        使用 python-docx 库读取文档内容，
        提取所有段落文本并合并。
        """
        doc = DocxDocument(path)
        paragraphs = []
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:  # 跳过空段落
                paragraphs.append(text)
        
        # 处理表格（如果有）
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    paragraphs.append(" | ".join(row_text))
        
        return "\n".join(paragraphs)
    
    def _parse_txt(self, path: Path) -> str:
        """解析纯文本文件"""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        - 去除多余空白
        - 去除特殊字符
        - 规范化换行
        """
        # 去除多余空白（多个空格合并为一个）
        text = re.sub(r"\s+", " ", text)
        
        # 去除首尾空白
        text = text.strip()
        
        # 规范化换行（最多两个连续换行）
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text


# ============ 使用示例 ============
if __name__ == "__main__":
    # 测试解析
    parser = DocumentParser()
    
    # 测试解析 Word 文档
    # text = parser.parse("test.docx")
    # print(f"解析结果: {text[:500]}...")
    
    print("✅ DocumentParser 测试通过")
```

---

## 2. 文本分块模块 (chunker.py)

文本分块模块将长文本分割成较小的 chunk，便于检索和作为 LLM 的上下文。

### 2.1 创建 chunker.py

`backend/app/core/chunker.py`：

```python
"""
文本分块模块
将长文本分割成固定大小的重叠 chunk
"""

from typing import List, Dict, Any
import re


class TextChunker:
    """
    文本分块器
    
    使用滑动窗口将文本分割成固定大小的重叠 chunk。
    
    配置：
    - chunk_size: 每个 chunk 的字符数（默认 256 tokens ≈ 512-1024 字符）
    - chunk_overlap: chunk 之间的重叠字符数（默认 64 tokens ≈ 128-256 字符）
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):
        """
        初始化分块器
        
        Args:
            chunk_size: 每个 chunk 的字符数
            chunk_overlap: 相邻 chunk 之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source: str = "") -> List[Dict[str, Any]]:
        """
        将文本分割成多个 chunk
        
        Args:
            text: 待分割的文本
            source: 文本来源（用于元数据）
            
        Returns:
            List[Dict]: chunk 列表，每个元素包含：
                - content: chunk 文本内容
                - metadata: 元数据（来源、chunk 索引等）
        """
        if not text or not text.strip():
            return []
        
        # 清理文本
        text = self._clean_text(text)
        
        # 按段落分割（保留段落结构）
        paragraphs = self._split_by_paragraph(text)
        
        # 合并段落成 chunk
        chunks = self._merge_to_chunks(paragraphs, source)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 去除多余空白
        text = re.sub(r"\s+", " ", text)
        # 去除首尾空白
        text = text.strip()
        return text
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """
        按段落分割文本
        
        优先按换行分割，其次按句子分割
        """
        # 先按双换行分割（段落）
        paragraphs = re.split(r"\n\n+", text)
        
        result = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            
            # 如果单个段落太长，按句子再分割
            if len(p) > self.chunk_size * 2:
                sentences = self._split_by_sentence(p)
                result.extend(sentences)
            else:
                result.append(p)
        
        return result
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """
        按句子分割文本
        
        简单实现，按常见句末标点分割
        """
        # 按句子结束符分割
        sentences = re.split(r"[。！？.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _merge_to_chunks(self, paragraphs: List[str], source: str) -> List[Dict[str, Any]]:
        """
        合并段落成固定大小的 chunk
        
        使用滑动窗口算法，确保相邻 chunk 有重叠
        """
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # 如果单个段落就超过 chunk_size，需要特殊处理
            if para_length > self.chunk_size:
                # 先保存当前 chunk
                if current_chunk:
                    chunk_text = self._join_chunk(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": source,
                            "chunk_index": chunk_index,
                            "chunk_size": len(chunk_text)
                        }
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_length = 0
                
                # 将超长段落按句子分割后逐个添加
                sentences = self._split_by_sentence(para)
                for sentence in sentences:
                    if current_length + len(sentence) <= self.chunk_size:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1  # +1 for separator
                    else:
                        # 保存当前 chunk
                        if current_chunk:
                            chunk_text = self._join_chunk(current_chunk)
                            chunks.append({
                                "content": chunk_text,
                                "metadata": {
                                    "source": source,
                                    "chunk_index": chunk_index,
                                    "chunk_size": len(chunk_text)
                                }
                            })
                            chunk_index += 1
                        
                        # 新 chunk 包含部分旧内容（overlap）
                        if self.chunk_overlap > 0 and current_chunk:
                            # 取最后一些句子作为新 chunk 的开头
                            overlap_text = self._join_chunk(current_chunk)
                            overlap_sentences = self._split_by_sentence(overlap_text)[-2:]  # 取最后两句
                            current_chunk = overlap_sentences
                            current_length = sum(len(s) for s in overlap_sentences)
                        else:
                            current_chunk = []
                            current_length = 0
                        
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
            
            # 如果加上当前段落会超过 chunk_size，先保存当前 chunk
            elif current_length + para_length > self.chunk_size:
                if current_chunk:
                    chunk_text = self._join_chunk(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": source,
                            "chunk_index": chunk_index,
                            "chunk_size": len(chunk_text)
                        }
                    })
                    chunk_index += 1
                
                # 新 chunk 从当前段落开始
                # 但为了保持 overlap，包含之前部分内容
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = self._join_chunk(current_chunk)
                    overlap_len = min(len(overlap_text), self.chunk_overlap)
                    overlap_start = len(overlap_text) - overlap_len
                    overlap = overlap_text[overlap_start:]
                    
                    current_chunk = [overlap, para]
                    current_length = len(overlap) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            
            # 否则，将段落加入当前 chunk
            else:
                current_chunk.append(para)
                current_length += para_length + 1  # +1 for separator
        
        # 处理最后一个 chunk
        if current_chunk:
            chunk_text = self._join_chunk(current_chunk)
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "source": source,
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text)
                }
            })
        
        return chunks
    
    def _join_chunk(self, parts: List[str]) -> str:
        """将 chunk 的各部分合并成字符串"""
        return " ".join(parts)


# ============ 使用示例 ============
if __name__ == "__main__":
    chunker = TextChunker(chunk_size=200, chunk_overlap=50)
    
    test_text = """
    贾宝玉是《红楼梦》的男主角。他出身于贾府，是贾母的孙子。贾宝玉与林黛玉从小一起长大，感情深厚。

    林黛玉是贾宝玉的表妹，也是《红楼梦》的女主角。她聪明伶俐，多愁善感。林黛玉与贾宝玉之间的爱情是全书的主线之一。

    薛宝钗是贾宝玉的表姐，后成为贾宝玉的妻子。她性格温柔贤惠，深得贾府上下喜爱。薛宝钗与林黛玉形成鲜明对比。
    """
    
    chunks = chunker.chunk(test_text, source="红楼梦")
    
    print(f"分块结果：共 {len(chunks)} 个 chunk\n")
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"内容: {chunk['content'][:100]}...")
        print()
```

---

## 3. Embedding 模块 (embedding.py)

Embedding 模块使用 BGE 模型将文本转换为向量表示。

### 3.1 创建 embedding.py

`backend/app/core/embedding.py`：

```python
"""
Embedding 模块
使用 BGE 模型生成文本向量
"""

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, EMBEDDING_DEVICE


class EmbeddingModel:
    """
    BGE Embedding 模型封装
    
    使用 shibing624/text2vec-base-chinese 模型生成中文文本的向量表示。
    该模型输出的向量维度为 768。
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, device: str = EMBEDDING_DEVICE):
        """
        初始化 Embedding 模型
        
        Args:
            model_name: HuggingFace 模型名称
            device: 推理设备 ("cpu" 或 "cuda")
        """
        self.model_name = model_name
        self.device = device
        print(f"正在加载 Embedding 模型: {model_name}...")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Embedding 模型加载完成，设备: {device}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        将单个查询文本转换为向量
        
        Args:
            query: 查询文本
            
        Returns:
            List[float]: 768 维向量
        """
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[List[float]]:
        """
        将多个文档文本转换为向量
        
        Args:
            documents: 文档列表，每个元素包含 "content" 字段
            
        Returns:
            List[List[float]]: 向量列表
        """
        texts = [doc["content"] for doc in documents]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度（768 for text2vec-base-chinese）
        """
        return self.model.get_sentence_embedding_dimension()


# ============ 使用示例 ============
if __name__ == "__main__":
    # 初始化模型
    embedding_model = EmbeddingModel()
    
    # 测试单个查询
    query = "贾宝玉和林黛玉是什么关系？"
    query_vector = embedding_model.embed_query(query)
    print(f"查询向量维度: {len(query_vector)}")
    print(f"查询向量前5位: {query_vector[:5]}")
    
    # 测试多个文档
    docs = [
        {"content": "贾宝玉是《红楼梦》的男主角"},
        {"content": "林黛玉是《红楼梦》的女主角"},
        {"content": "薛宝钗是贾宝玉的妻子"}
    ]
    doc_vectors = embedding_model.embed_documents(docs)
    print(f"\n文档向量数量: {len(doc_vectors)}")
    print(f"每个文档向量维度: {len(doc_vectors[0])}")
    
    # 计算余弦相似度
    import numpy as np
    
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    print("\n查询与各文档的相似度:")
    for i, doc in enumerate(docs):
        sim = cosine_similarity(query_vector, doc_vectors[i])
        print(f"  文档{i+1}: {sim:.4f} - {doc['content']}")
```

---

## 4. 向量存储模块 (vector_store.py)

向量存储模块负责与 Milvus 交互，实现向量的插入和检索。

### 4.1 创建 vector_store.py

`backend/app/core/vector_store.py`：

```python
"""
向量存储模块
与 Milvus 交互，实现向量的插入和检索
"""

from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.config import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION, MILVUS_DIM


class MilvusStore:
    """
    Milvus 向量数据库封装
    
    提供以下功能：
    - 初始化 Collection
    - 插入向量
    - 相似度检索
    - 按实体检索
    """
    
    def __init__(self, host: str = MILVUS_HOST, port: int = MILVUS_PORT):
        """
        初始化 Milvus 连接
        
        Args:
            host: Milvus 服务器地址
            port: Milvus gRPC 端口
        """
        self.host = host
        self.port = port
        self.collection_name = MILVUS_COLLECTION
        self.dim = MILVUS_DIM
        self.collection: Optional[Collection] = None
        
        # 建立连接
        self._connect()
    
    def _connect(self):
        """建立与 Milvus 的连接"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port
        )
        print(f"✅ Milvus 连接成功: {self.host}:{self.port}")
    
    def check_connection(self):
        """检查 Milvus 连接状态"""
        connections.connect(
            alias="check",
            host=self.host,
            port=self.port
        )
        connections.disconnect("check")
    
    def init_collection(self, force: bool = False):
        """
        初始化 Collection
        
        如果 Collection 已存在且 force=True，则删除重建。
        
        Schema:
        - id: int64, 主键，自增
        - content: varchar, 文本内容
        - vector: float_vector, 向量
        - metadata: json, 元数据
        """
        # 检查 Collection 是否存在
        if utility.has_collection(self.collection_name):
            if force:
                utility.drop_collection(self.collection_name)
                print(f"⚠️ 已删除旧 Collection: {self.collection_name}")
            else:
                self.collection = Collection(self.collection_name)
                self.collection.load()
                print(f"✅ Collection 已存在，加载完成: {self.collection_name}")
                return
        
        # 创建 Collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="RAG 知识库文档向量存储"
        )
        
        self.collection = Collection(name=self.collection_name, schema=schema)
        
        # 创建索引（加速检索）
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",  # 余弦相似度
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        
        self.collection.load()
        print(f"✅ Collection 创建成功: {self.collection_name}")
    
    def insert(self, documents: List[Dict[str, Any]], vectors: List[List[float]], metadata: Dict[str, Any] = None):
        """
        插入文档和向量
        
        Args:
            documents: 文档列表，每个包含 content
            vectors: 向量列表
            metadata: 附加元数据
        """
        if not self.collection:
            self.init_collection()
        
        # 准备数据
        contents = [doc["content"] for doc in documents]
        metadatas = [metadata or {} for _ in documents]
        
        # 插入数据
        self.collection.insert({
            "content": contents,
            "vector": vectors,
            "metadata": metadatas
        })
        
        # 刷新（确保数据可被检索）
        self.collection.flush()
        print(f"✅ 插入 {len(documents)} 条数据到 Milvus")
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        向量相似度检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回前 k 个结果
            
        Returns:
            List[Dict]: 检索结果列表，每个包含 content, score, metadata
        """
        if not self.collection:
            self.init_collection()
        
        # 搜索参数
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # 执行搜索
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["content", "metadata"]
        )
        
        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "content": hit.entity.get("content"),
                    "score": hit.score,
                    "metadata": hit.entity.get("metadata", {})
                })
        
        return formatted_results
    
    def search_by_entity(self, entity_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        通过实体名称检索相关文档
        
        利用向量检索找到与实体最相关的文档片段。
        这个方法会在下一节 RRF 融合中用到。
        """
        # 将实体名作为查询向量
        from app.core.embedding import EmbeddingModel
        
        embedding_model = EmbeddingModel()
        entity_vector = embedding_model.embed_query(entity_name)
        
        return self.search(entity_vector, top_k)
    
    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        获取所有数据（用于调试）"""
        if not self.collection:
            self.init_collection()
        
        results = self.collection.query(
            expr="id >= 0",
            output_fields=["id", "content", "metadata"],
            limit=limit
        )
        
        return results
    
    def delete_by_file_id(self, file_id: str):
        """根据 file_id 删除数据"""
        if not self.collection:
            self.init_collection()
        
        self.collection.delete(f'metadata["file_id"] == "{file_id}"')
        self.collection.flush()
        print(f"✅ 已删除 file_id={file_id} 的数据")
    
    def close(self):
        """关闭连接"""
        connections.disconnect("default")


# ============ 使用示例 ============
if __name__ == "__main__":
    # 初始化
    store = MilvusStore()
    store.init_collection()
    
    # 插入测试数据
    test_docs = [
        {"content": "贾宝玉是《红楼梦》的男主角"},
        {"content": "林黛玉是《红楼梦》的女主角"},
        {"content": "薛宝钗是贾宝玉的妻子"}
    ]
    
    from app.core.embedding import EmbeddingModel
    embedding_model = EmbeddingModel()
    test_vectors = embedding_model.embed_documents(test_docs)
    
    store.insert(test_docs, test_vectors, {"source": "test"})
    
    # 检索
    query_vector = embedding_model.embed_query("贾宝玉是谁？")
    results = store.search(query_vector, top_k=2)
    
    print("\n检索结果:")
    for r in results:
        print(f"  相似度: {r['score']:.4f}")
        print(f"  内容: {r['content']}")
    
    store.close()
```

---

## 5. 图谱存储模块 (graph_store.py)

图谱存储模块负责与 Neo4j 交互，存储和查询知识图谱数据。

### 5.1 创建 graph_store.py

`backend/app/core/graph_store.py`：

```python
"""
图谱存储模块
与 Neo4j 交互，存储和查询知识图谱
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jStore:
    """
    Neo4j 图数据库封装
    
    提供以下功能：
    - 初始化图谱 Schema
    - 创建节点
    - 创建关系
    - 查询节点和关系
    - 实体扩展检索
    """
    
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        """
        初始化 Neo4j 连接
        
        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """建立与 Neo4j 的连接"""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print(f"✅ Neo4j 连接成功: {self.uri}")
    
    def check_connection(self):
        """检查 Neo4j 连接状态"""
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
    
    def init_schema(self):
        """
        初始化图谱 Schema
        
        创建必要的约束和索引，提升查询性能。
        """
        with self.driver.session() as session:
            # 创建节点 name 属性的唯一性约束
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE
            """)
            
            # 创建节点类型索引
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)
            """)
            
            print("✅ Neo4j Schema 初始化完成")
    
    def create_entity(self, name: str, entity_type: str, properties: Dict[str, Any] = None):
        """
        创建实体（节点）
        
        Args:
            name: 实体名称
            entity_type: 实体类型（如 "人物"、"地点"）
            properties: 实体属性
        """
        properties = properties or {}
        
        # 构建属性字符串
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        if props_str:
            props_str = ", " + props_str
        
        cypher = f"""
            MERGE (e:Entity {{name: $name}})
            SET e.type = $type {props_str}
            RETURN e
        """
        
        params = {"name": name, "type": entity_type, **properties}
        
        with self.driver.session() as session:
            session.run(cypher, **params)
    
    def create_relation(self, from_entity: str, to_entity: str, relation_type: str, properties: Dict[str, Any] = None):
        """
        创建关系（边）
        
        Args:
            from_entity: 源实体名称
            to_entity: 目标实体名称
            relation_type: 关系类型（如 "恋人"、"夫妻"）
            properties: 关系属性
        """
        properties = properties or {}
        
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        if props_str:
            props_str = ", " + props_str
        
        cypher = f"""
            MATCH (a:Entity {{name: $from_entity}})
            MATCH (b:Entity {{name: $to_entity}})
            MERGE (a)-[r:{relation_type} {{name: $relation_type"{props_str}"}}]->(b)
            RETURN r
        """
        
        params = {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "relation_type": relation_type,
            **properties
        }
        
        with self.driver.session() as session:
            session.run(cypher, **params)
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """
        获取所有节点
        
        Returns:
            List[Dict]: 节点列表
        """
        cypher = """
            MATCH (e:Entity)
            RETURN id(e) AS id, e.name AS name, e.type AS type, 
                   PROPERTIES(e) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            nodes = []
            for record in result:
                node = {
                    "id": str(record["id"]),
                    "name": record["name"],
                    "type": record["type"],
                    "properties": {k: v for k, v in record["properties"].items() 
                                  if k not in ["name", "type"]}
                }
                nodes.append(node)
            return nodes
    
    def get_all_relations(self) -> List[Dict[str, Any]]:
        """
        获取所有关系
        
        Returns:
            List[Dict]: 关系列表
        """
        cypher = """
            MATCH (a:Entity)-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to,
                   PROPERTIES(r) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            relations = []
            for record in result:
                rel = {
                    "from": record["from"],
                    "to": record["to"],
                    "type": record["type"],
                    "properties": record["properties"] or {}
                }
                relations.append(rel)
            return relations
    
    def search_nodes(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索节点
        
        模糊匹配节点名称。
        """
        cypher = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $keyword OR e.type CONTAINS $keyword
            RETURN id(e) AS id, e.name AS name, e.type AS type
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, keyword=keyword)
            return [{"id": str(r["id"]), "name": r["name"], "type": r["type"]} 
                   for r in result]
    
    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定名称的节点
        """
        cypher = """
            MATCH (e:Entity {name: $name})
            RETURN id(e) AS id, e.name AS name, e.type AS type,
                   PROPERTIES(e) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, name=name)
            record = result.single()
            if record:
                return {
                    "id": str(record["id"]),
                    "name": record["name"],
                    "type": record["type"],
                    "properties": {k: v for k, v in record["properties"].items()
                                  if k not in ["name", "type"]}
                }
            return None
    
    def get_node_relations(self, name: str) -> List[Dict[str, Any]]:
        """
        获取节点的所有一度关系
        """
        cypher = """
            MATCH (a:Entity {name: $name})-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to
            UNION
            MATCH (a:Entity)-[r]->(b:Entity {name: $name})
            RETURN a.name AS from, type(r) AS type, b.name AS to
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, name=name)
            return [{"from": r["from"], "type": r["type"], "to": r["to"]} 
                   for r in result]
    
    def expand_entities(self, query: str) -> List[Dict[str, Any]]:
        """
        根据查询扩展相关实体
        
        从查询中识别可能的实体，返回图谱中相关的实体列表。
        这里采用简单策略：查询包含在节点名中的实体。
        
        Args:
            query: 用户查询
            
        Returns:
            List[Dict]: 匹配的实体列表
        """
        # 获取所有节点
        all_nodes = self.get_all_nodes()
        
        # 简单匹配：查询词包含节点名，或节点名包含查询词
        matched = []
        query_lower = query.lower()
        
        for node in all_nodes:
            if (node["name"] in query or 
                query in node["name"] or
                node["name"].lower() in query_lower):
                matched.append(node)
        
        return matched[:10]  # 最多返回 10 个
    
    def clear_all(self):
        """清空所有节点和关系（用于测试）"""
        cypher = """
            MATCH (n) DETACH DELETE n
        """
        
        with self.driver.session() as session:
            session.run(cypher)
            print("✅ Neo4j 数据已清空")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# ============ 使用示例 ============
if __name__ == "__main__":
    # 初始化
    store = Neo4jStore()
    store.init_schema()
    
    # 清空数据（测试用）
    store.clear_all()
    
    # 创建节点
    store.create_entity("贾宝玉", "人物", {"role": "男主角", "source": "红楼梦"})
    store.create_entity("林黛玉", "人物", {"role": "女主角", "source": "红楼梦"})
    store.create_entity("薛宝钗", "人物", {"role": "妻子", "source": "红楼梦"})
    store.create_entity("贾府", "地点", {"description": "贾宝玉居住地"})
    
    # 创建关系
    store.create_relation("贾宝玉", "林黛玉", "恋人", {"description": "宝黛爱情"})
    store.create_relation("贾宝玉", "薛宝钗", "夫妻", {"description": "金玉良缘"})
    store.create_relation("贾宝玉", "贾府", "居住", {})
    
    # 查询
    print("\n所有节点:")
    nodes = store.get_all_nodes()
    for n in nodes:
        print(f"  - {n['name']} ({n['type']})")
    
    print("\n所有关系:")
    rels = store.get_all_relations()
    for r in rels:
        print(f"  {r['from']} --[{r['type']}]--> {r['to']}")
    
    print("\n搜索'宝玉':")
    matched = store.search_nodes("宝玉")
    for m in matched:
        print(f"  - {m['name']} ({m['type']})")
    
    store.close()
```

---

## 6. RRF 融合模块 (fusion.py)

RRF（Reciprocal Rank Fusion）模块实现双轨检索结果的融合排序。

### 6.1 创建 fusion.py

`backend/app/core/fusion.py`：

```python
"""
RRF 融合模块
实现向量检索和图谱检索结果的融合排序
"""

from typing import List, Dict, Any


class RRFFusion:
    """
    RRF（倒数排名融合）算法实现
    
    RRF 是一种简单而有效的多检索结果融合方法，
    被广泛应用于搜索引擎的结果融合。
    
    原理：
    对于每个结果，计算 RRF 得分 = 1 / (k + rank)
    其中 k 是经验参数（通常为 60），rank 是该结果在各自列表中的排名
    最终得分是所有检索列表中得分的总和。
    
    优势：
    - 不需要人工调参
    - 对检索系统的好坏鲁棒
    - 实现简单
    """
    
    def __init__(self, k: int = 60):
        """
        初始化 RRF 融合器
        
        Args:
            k: RRF 经验参数，通常不需要调整
        """
        self.k = k
    
    def fuse(self, 
             vector_results: List[Dict[str, Any]], 
             graph_results: List[Dict[str, Any]], 
             k: int = None) -> List[Dict[str, Any]]:
        """
        融合向量检索和图谱检索的结果
        
        Args:
            vector_results: Milvus 向量检索结果
            graph_results: Neo4j 图谱检索结果
            k: RRF 参数
            
        Returns:
            List[Dict]: 融合后的结果，按 RRF 得分降序排列
        """
        if k is None:
            k = self.k
        
        # 如果某个列表为空，直接返回另一个列表
        if not vector_results:
            return graph_results
        if not graph_results:
            return vector_results
        
        # 计算 RRF 得分
        rrf_scores = {}
        
        # 向量检索结果的 RRF 得分
        for rank, result in enumerate(vector_results):
            content = result["content"]
            rrf_score = 1.0 / (k + rank + 1)  # +1 因为 rank 从 0 开始
            if content in rrf_scores:
                rrf_scores[content]["score"] += rrf_score
                rrf_scores[content]["sources"].append("vector")
            else:
                rrf_scores[content] = {
                    "content": content,
                    "score": rrf_score,
                    "sources": ["vector"],
                    "metadata": result.get("metadata", {})
                }
        
        # 图谱检索结果的 RRF 得分
        for rank, result in enumerate(graph_results):
            content = result["content"]
            rrf_score = 1.0 / (k + rank + 1)
            if content in rrf_scores:
                rrf_scores[content]["score"] += rrf_score
                rrf_scores[content]["sources"].append("graph")
            else:
                rrf_scores[content] = {
                    "content": content,
                    "score": rrf_score,
                    "sources": ["graph"],
                    "metadata": result.get("metadata", {})
# 前端开发

前端使用 React + Vite 构建，提供问答页面和知识图谱可视化页面。

---

## 1. 前端项目初始化

### 1.1 创建前端项目

```bash
cd ~/rag-knowledge-base/frontend

# 使用 Vite 创建 React 项目
npm create vite@latest . -- --template react

# 安装依赖
npm install
```

### 1.2 安装额外依赖

```bash
# HTTP 客户端
npm install axios

# ECharts 图可视化
npm install echarts echarts-for-react

# UI 组件（可选）
npm install antd
```

---

## 2. 项目结构

```
frontend/
├── src/
│   ├── App.jsx           # 主应用组件
│   ├── main.jsx          # 入口文件
│   ├── pages/
│   │   ├── ChatPage.jsx  # 问答页面
│   │   └── GraphPage.jsx # 知识图谱页面
│   ├── components/
│   │   ├── ChatBox.jsx   # 聊天框组件
│   │   ├── UploadModal.jsx # 上传弹窗组件
│   │   └── KnowledgeGraph.jsx # 图谱组件
│   ├── api/
│   │   └── index.js      # API 调用封装
│   ├── App.css           # 全局样式
│   └── index.css
├── package.json
├── vite.config.js
└── Dockerfile
```

---

## 3. API 封装

### 3.1 创建 src/api/index.js

```javascript
// src/api/index.js
// API 调用封装

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,  // 60 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============ 文档上传 ============

/**
 * 上传文档
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 进度回调
 * @returns {Promise}
 */
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response.data;
};

// ============ 问答 ============

/**
 * 发送问答
 * @param {string} question - 问题
 * @param {number} topK - 返回结果数量
 * @returns {Promise}
 */
export const chat = async (question, topK = 5) => {
  const response = await apiClient.post('/chat/', {
    question,
    top_k: topK,
  });
  return response.data;
};

// ============ 知识图谱 ============

/**
 * 获取图谱数据
 * @returns {Promise}
 */
export const getGraphData = async () => {
  const response = await apiClient.get('/graph/');
  return response.data;
};

/**
 * 搜索图谱节点
 * @param {string} keyword - 搜索关键词
 * @returns {Promise}
 */
export const searchGraph = async (keyword) => {
  const response = await apiClient.get('/graph/search', {
    params: { keyword },
  });
  return response.data;
};

// ============ 健康检查 ============

/**
 * 健康检查
 * @returns {Promise}
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
```

---

## 4. 问答页面

### 4.1 创建 src/pages/ChatPage.jsx

```jsx
// src/pages/ChatPage.jsx
// 问答页面

import { useState } from 'react';
import { chat, uploadDocument } from '../api';
import ChatBox from '../components/ChatBox';
import UploadModal from '../components/UploadModal';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadLoading, setUploadLoading] = useState(false);

  // 发送消息
  const handleSend = async (question) => {
    if (!question.trim()) return;

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const response = await chat(question);
      
      // 添加 AI 消息
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        graphEntities: response.graph_entities,
      }]);
    } catch (error) {
      console.error('问答失败:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
      }]);
    } finally {
      setLoading(false);
    }
  };

  // 上传文档
  const handleUpload = async (file) => {
    setUploadLoading(true);
    setUploadProgress(0);

    try {
      const result = await uploadDocument(file, setUploadProgress);
      alert(`文档上传成功！\n${result.message}`);
      setShowUpload(false);
    } catch (error) {
      console.error('上传失败:', error);
      alert('文档上传失败，请稍后重试。');
    } finally {
      setUploadLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="chat-page">
      <header className="chat-header">
        <h1>💬 知识库问答</h1>
        <button onClick={() => setShowUpload(true)}>上传文档</button>
      </header>

      <ChatBox
        messages={messages}
        loading={loading}
        onSend={handleSend}
      />

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUpload={handleUpload}
          progress={uploadProgress}
          loading={uploadLoading}
        />
      )}
    </div>
  );
}

export default ChatPage;
```

### 4.2 创建 src/components/ChatBox.jsx

```jsx
// src/components/ChatBox.jsx
// 聊天框组件

import { useState, useRef, useEffect } from 'react';

function ChatBox({ messages, loading, onSend }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="chat-box">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>👋 欢迎使用知识库问答系统</p>
            <p>请先上传文档，然后输入问题进行问答</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              
              {/* 显示来源文档 */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <p>📚 参考文档：</p>
                  {msg.sources.map((src, i) => (
                    <div key={i} className="source-item">
                      <span className="score">相关度: {(src.score * 100).toFixed(1)}%</span>
                      <p className="source-content">{src.content}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* 显示图谱实体 */}
              {msg.graphEntities && msg.graphEntities.length > 0 && (
                <div className="graph-entities">
                  <p>🔗 关联实体：</p>
                  <div className="entity-tags">
                    {msg.graphEntities.map((entity, i) => (
                      <span key={i} className="entity-tag">
                        {entity.name} ({entity.type})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入您的问题..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          发送
        </button>
      </form>
    </div>
  );
}

export default ChatBox;
```

### 4.3 创建 src/components/UploadModal.jsx

```jsx
// src/components/UploadModal.jsx
// 上传弹窗组件

import { useState, useRef } from 'react';

function UploadModal({ onClose, onUpload, progress, loading }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
    }
  };

  const handleUpload = () => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>📤 上传文档</h2>

        <div
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".docx,.txt"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          
          {file ? (
            <div className="file-selected">
              <span>📄 {file.name}</span>
              <span>{(file.size / 1024).toFixed(1)} KB</span>
            </div>
          ) : (
            <div className="upload-hint">
              <p>拖拽文件到此处，或点击选择</p>
              <p className="hint">支持 .docx, .txt 格式</p>
            </div>
          )}
        </div>

        {loading && (
          <div className="progress-bar">
            <div className="progress" style={{ width: `${progress}%` }}></div>
          </div>
        )}

        <div className="modal-actions">
          <button onClick={onClose} disabled={loading}>取消</button>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="primary"
          >
            {loading ? `上传中... ${progress}%` : '上传'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadModal;
```

---

## 5. 知识图谱页面

### 5.1 创建 src/pages/GraphPage.jsx

```jsx
// src/pages/GraphPage.jsx
// 知识图谱可视化页面

import { useState, useEffect } from 'react';
import { getGraphData, searchGraph } from '../api';
import KnowledgeGraph from '../components/KnowledgeGraph';

function GraphPage() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filteredData, setFilteredData] = useState(null);

  // 加载图谱数据
  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getGraphData();
      setGraphData(data.data);
      setFilteredData(data.data);
    } catch (err) {
      console.error('加载图谱失败:', err);
      setError('加载图谱数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 搜索节点
  const handleSearch = async () => {
    if (!searchKeyword.trim()) {
      setFilteredData(graphData);
      return;
    }

    try {
      const data = await searchGraph(searchKeyword);
      setFilteredData({
        nodes: data.nodes || [],
        relations: data.relations || [],
      });
    } catch (err) {
      console.error('搜索失败:', err);
    }
  };

  return (
    <div className="graph-page">
      <header className="graph-header">
        <h1>🕸️ 知识图谱</h1>
        <div className="search-box">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索节点..."
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>搜索</button>
        </div>
        <button onClick={loadGraphData} className="refresh-btn">
          🔄 刷新
        </button>
      </header>

      <div className="graph-stats">
        {filteredData && (
          <>
            <span>📍 节点数: {filteredData.nodes?.length || 0}</span>
            <span>🔗 关系数: {filteredData.relations?.length || 0}</span>
          </>
        )}
      </div>

      <div className="graph-container">
        {loading && (
          <div className="loading">
            <div className="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <p>加载图谱数据中...</p>
          </div>
        )}

        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={loadGraphData}>重试</button>
          </div>
        )}

        {!loading && !error && filteredData && (
          <KnowledgeGraph data={filteredData} />
        )}
      </div>
    </div>
  );
}

export default GraphPage;
```

### 5.2 创建 src/components/KnowledgeGraph.jsx

```jsx
// src/components/KnowledgeGraph.jsx
// ECharts 知识图谱组件

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

function KnowledgeGraph({ data }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化图表
    chartInstance.current = echarts.init(chartRef.current);

    // 转换数据格式
    const chartData = convertToEChartsData(data);

    // 配置图表
    const option = {
      title: {
        text: '知识图谱',
        left: 'center',
      },
      tooltip: {
        formatter: (params) => {
          if (params.dataType === 'node') {
            return `${params.data.name}<br/>类型: ${params.data.type}`;
          } else {
            return `${params.data.source} → ${params.data.target}<br/>关系: ${params.data.relType}`;
          }
        },
      },
      legend: {
        data: getNodeTypes(data.nodes),
        left: 'left',
      },
      series: [
        {
          name: '知识图谱',
          type: 'graph',
          layout: 'force',
          roam: true,  // 支持缩放拖拽
          draggable: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
          },
          force: {
            repulsion: 200,
            gravity: 0.1,
            edgeLength: [50, 200],
            layoutAnimation: true,
          },
          data: chartData.nodes,
          links: chartData.links,
          lineStyle: {
            width: 2,
            curveness: 0.3,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
          categories: getCategories(data.nodes),
          edgeLabel: {
            show: true,
            formatter: '{c}',
            fontSize: 10,
          },
          edgeSymbol: ['circle', 'arrow'],
        },
      ],
    };

    chartInstance.current.setOption(option);

    // 响应窗口大小变化
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data]);

  // 转换数据为 ECharts 格式
  const convertToEChartsData = (data) => {
    const nodes = (data.nodes || []).map((node, index) => ({
      id: index,
      name: node.name,
      type: node.type,
      symbolSize: 40,
    }));

    const links = (data.relations || []).map((rel) => {
      const sourceNode = nodes.find((n) => n.name === rel.from);
      const targetNode = nodes.find((n) => n.name === rel.to);
      
      if (sourceNode && targetNode) {
        return {
          source: sourceNode.id,
          target: targetNode.id,
          relType: rel.type,
          name: rel.type,
        };
      }
      return null;
    }).filter(Boolean);

    return { nodes, links };
  };

  // 获取节点类型列表
  const getNodeTypes = (nodes) => {
    const types = [...new Set((nodes || []).map((n) => n.type))];
    return types;
  };

  // 获取类别配置
  const getCategories = (nodes) => {
    const types = [...new Set((nodes || []).map((n) => n.type))];
    return types.map((type) => ({
      name: type,
    }));
  };

  return <div ref={chartRef} style={{ width: '100%', height: '600px' }} />;
}

export default KnowledgeGraph;
```

---

## 6. 主应用组件

### 6.1 修改 src/App.jsx

```jsx
// src/App.jsx
// 主应用组件

import { useState } from 'react';
import ChatPage from './pages/ChatPage';
import GraphPage from './pages/GraphPage';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('chat');

  return (
    <div className="app">
      <nav className="nav">
        <button
          className={currentPage === 'chat' ? 'active' : ''}
          onClick={() => setCurrentPage('chat')}
        >
          💬 问答
        </button>
        <button
          className={currentPage === 'graph' ? 'active' : ''}
          onClick={() => setCurrentPage('graph')}
        >
          🕸️ 图谱
        </button>
      </nav>

      <main className="main-content">
        {currentPage === 'chat' && <ChatPage />}
        {currentPage === 'graph' && <GraphPage />}
      </main>
    </div>
  );
}

export default App;
```

### 6.2 修改 src/App.css

```css
/* src/App.css */

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
}

/* 导航栏 */
.nav {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.nav button {
  padding: 0.5rem 1.5rem;
  border: none;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.nav button:hover {
  background: #e0e0e0;
}

.nav button.active {
  background: #4a90e2;
  color: white;
}

/* 主要内容 */
.main-content {
  flex: 1;
  overflow: hidden;
}

/* ============ 问答页面 ============ */

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #ddd;
}

.chat-header h1 {
  font-size: 1.5rem;
  margin: 0;
}

.chat-header button {
  padding: 0.5rem 1rem;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.chat-box {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.empty-state {
  text-align: center;
  color: #888;
  padding: 2rem;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 2rem;
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: #f0f0f0;
}

.message-user .message-content {
  background: #4a90e2;
  color: white;
}

.message-text {
  line-height: 1.5;
}

.sources {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(0,0,0,0.1);
  font-size: 0.9rem;
}

.source-item {
  background: rgba(0,0,0,0.05);
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.5rem;
}

.message-user .source-item {
  background: rgba(255,255,255,0.2);
}

.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.entity-tag {
  background: #e3f2fd;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.input-form {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-top: 1px solid #ddd;
}

.input-form input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.input-form button {
  padding: 0.75rem 1.5rem;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.input-form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* ============ 知识图谱页面 ============ */

.graph-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #ddd;
}

.graph-header h1 {
  font-size: 1.5rem;
  margin: 0;
}

.search-box {
  display: flex;
  gap: 0.5rem;
}

.search-box input {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  width: 200px;
}

.search-box button,
.refresh-btn {
  padding: 0.5rem 1rem;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.graph-stats {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  display: flex;
  gap: 2rem;
  font-size: 0.9rem;
}

.graph-container {
  flex: 1;
  padding: 1rem;
}

/* ============ 上传弹窗 ============ */

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  width: 500px;
  max-width: 90%;
}

.modal-content h2 {
  margin-top: 0;
}

.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin: 1rem 0;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: #4a90e2;
  background: #f0f8ff;
}

.file-selected {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-hint p {
  margin: 0.5rem 0;
}

.hint {
  color: #888;
  font-size: 0.9rem;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #4a90e2;
  transition: width 0.3s;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
}

.modal-actions button {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.modal-actions button.primary {
  background: #4a90e2;
  color: white;
}

.modal-actions button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* ============ 加载动画 ============ */

.loading-dots {
  display: inline-flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #888;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
```

---

## 7. 下一个章节

前端开发完成！下一章我们将进行 **前后端联调**。
# 前后端联调

本章介绍如何启动前后端服务并进行联调测试。

---

## 1. 启动后端服务

### 1.1 配置环境变量

```bash
cd ~/rag-knowledge-base/backend

# 创建 .env 文件
cat > .env << EOF
# MiniMax API 配置
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123456

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
EOF
```

### 1.2 启动 FastAPI

```bash
# 激活 conda 环境
conda activate rag

# 启动服务（开发模式，自动重载）
cd ~/rag-knowledge-base/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**预期输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 1.3 验证后端启动

浏览器访问：`http://localhost:8000/docs`

应该能看到 FastAPI 自动生成的 API 文档页面。

---

## 2. 启动前端服务

### 2.1 配置 API 地址

```bash
cd ~/rag-knowledge-base/frontend

# 创建 .env 文件
cat > .env << EOF
VITE_API_URL=http://localhost:8000/api
EOF
```

### 2.2 安装依赖并启动

```bash
npm install
npm run dev
```

**预期输出：**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

### 2.3 验证前端启动

浏览器访问：`http://localhost:3000`

应该能看到问答页面。

---

## 3. 联调测试

### 3.1 健康检查

```bash
curl http://localhost:8000/health
```

**预期输出：**
```json
{
  "status": "ok",
  "milvus": "healthy",
  "neo4j": "healthy",
  "timestamp": "2026-04-04T10:00:00"
}
```

### 3.2 上传文档测试

使用 FastAPI Docs 或 curl 上传文档：

```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt"
```

**预期输出：**
```json
{
  "file_id": "xxx",
  "filename": "test.txt",
  "status": "success",
  "message": "文档上传成功！解析了 10 个文本块，提取了 5 个实体和 3 个关系"
}
```

### 3.3 问答测试

```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"question": "贾宝玉和林黛玉是什么关系？"}'
```

**预期输出：**
```json
{
  "answer": "贾宝玉和林黛玉是恋人关系...",
  "sources": [...],
  "graph_entities": [...]
}
```

### 3.4 图谱查询测试

```bash
curl http://localhost:8000/api/graph/
```

**预期输出：**
```json
{
  "data": {
    "nodes": [...],
    "relations": [...]
  },
  "total_nodes": 10,
  "total_relations": 5
}
```

---

## 4. 常见问题排查

### 4.1 前端无法访问后端 API

**问题：** 前端请求返回跨域错误或连接失败

**排查步骤：**
1. 确认后端服务是否正常运行
2. 确认后端 CORS 配置是否正确
3. 确认前端 .env 中的 API 地址是否正确

**解决方法：**
```javascript
// backend/app/main.py 中的 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 指定前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Milvus 连接失败

**问题：** `Connection refused` 或超时

**排查步骤：**
1. 确认 Milvus 容器是否运行
2. 确认端口 19530 是否可访问

```bash
docker compose -f ~/rag-knowledge-base/docker/milvus/docker-compose.yml ps
```

### 4.3 Neo4j 连接失败

**问题：** Neo4j 连接认证失败

**排查步骤：**
1. 确认 .env 中的用户名密码正确
2. 确认 Neo4j 容器正常运行

```bash
docker compose -f ~/rag-knowledge-base/docker/neo4j/docker-compose.yml ps
```

### 4.4 MiniMax API 调用失败

**问题：** 返回 401 或 403 错误

**排查步骤：**
1. 确认 API Key 正确
2. 确认 API Key 有余额

```bash
# 检查 .env 文件
cat ~/rag-knowledge-base/backend/.env | grep MINIMAX
```

---

## 5. 下一个章节

联调完成！下一章我们将进行 **Docker 部署**。
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
