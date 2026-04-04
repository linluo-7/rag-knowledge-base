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
