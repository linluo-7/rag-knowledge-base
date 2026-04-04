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
