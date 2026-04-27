# RAG 知识库系统

> 基于 LangChain + Milvus + Neo4j 的 RAG 知识库问答系统，支持知识图谱构建与双轨检索融合

## 版本

**v2.0.0** - 工业级重构版本

## 功能特性

- 📄 **文档上传解析** — 支持 Word (.docx)、纯文本 (.txt) 文档上传与内容提取
- 🔍 **向量检索** — Milvus 向量数据库存储 + BGE 中文 Embedding 模型
- 🕸️ **知识图谱** — Neo4j 图数据库存储实体关系，LLM 自动提取
- 💬 **智能问答** — 双轨检索（向量+图谱）+ RRF 融合 + LLM 生成答案
- 📊 **图谱可视化** — ECharts 力导向图展示实体关系网络
- 🐳 **一键部署** — Docker Compose 快速启动全部组件
- 🔒 **认证限流** — API Key 认证 + 请求限流
- 📈 **监控告警** — 健康检查 + 指标监控

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│   问答页面 + 知识图谱可视化 (ECharts)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / API
┌──────────────────────────▼──────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 文档解析  │  │ 文本分块  │  │ Embedding│  │ LLM 调用 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ RRF 融合  │  │ 向量存储  │  │ 图谱存储  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Milvus  │    │   Neo4j  │    │ MiniMax  │
    │ 向量数据库│    │ 图数据库  │    │  LLM API │
    └──────────┘    └──────────┘    └──────────┘
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/linluo-7/rag-knowledge-base.git
cd rag-knowledge-base
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env，填入你的 MiniMax API Key
```

### 3. 启动服务

```bash
# 一键启动全部服务（推荐）
docker compose -f docker/docker-compose.prod.yml up -d

# 或分步启动
docker compose -f docker/docker-compose.prod.yml up -d milvus neo4j redis
cd backend
python -m uvicorn app.main:app --port 5003
```

### 4. 访问系统

- 前端界面：http://localhost:5004
- 后端 API：http://localhost:5003
- API 文档：http://localhost:5003/docs
- Neo4j Browser：http://localhost:7474

## 项目结构

```
rag-knowledge-base/
├── app/                         # FastAPI 后端
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理（Pydantic Settings）
│   ├── factory.py              # 依赖注入工厂
│   ├── exceptions.py           # 自定义异常
│   ├── logging.py              # 日志配置
│   │
│   ├── core/                   # 基础设施层
│   │   ├── vector_store/       # 向量存储（抽象接口 + Milvus 实现）
│   │   ├── graph_store/        # 图存储（抽象接口 + Neo4j 实现）
│   │   ├── llm/               # LLM（抽象接口 + MiniMax 实现）
│   │   ├── embedding.py       # BGE Embedding
│   │   ├── chunker.py         # 文本分块
│   │   ├── document.py        # 文档解析
│   │   ├── fusion.py          # RRF 融合
│   │   └── cache.py          # Redis 缓存
│   │
│   ├── service/               # 业务层
│   │   ├── rag_service.py    # RAG 服务
│   │   └── document_service.py  # 文档服务
│   │
│   ├── api/                  # 入口层
│   │   ├── chat.py          # 问答接口
│   │   ├── upload.py        # 上传接口
│   │   └── graph.py         # 图谱接口
│   │
│   └── schemas/             # 数据模型
│       ├── request.py
│       └── response.py
│
├── frontend/                  # React 前端
├── docker/                   # Docker 配置
│   ├── Dockerfile
│   └── docker-compose.prod.yml
└── docs/                     # 开发文档
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/v1/upload/` | 上传文档 | 解析文档，存入向量库和图谱 |
| `POST /api/v1/chat/` | 问答 | 输入问题，返回答案和相关文档 |
| `GET /api/v1/graph/` | 获取图谱 | 返回所有实体和关系 |
| `GET /api/v1/graph/search` | 搜索图谱 | 按关键词搜索相关实体 |
| `GET /health` | 健康检查 | 检查 Milvus 和 Neo4j 状态 |

## 工业级特性

### 代码质量

- ✅ 配置中心化（Pydantic Settings）
- ✅ 依赖注入工厂（单例模式）
- ✅ 自定义异常体系
- ✅ 结构化日志系统
- ✅ 分层架构（API / Service / Core）

### 核心模块

- ✅ VectorStore 抽象接口 + Milvus 实现
- ✅ GraphStore 抽象接口 + Neo4j 实现
- ✅ LLM 抽象接口 + MiniMax 实现（支持 API Key 轮换）
- ✅ Embedding 模型单例化
- ✅ Redis 缓存层

### 业务层

- ✅ RAG 服务（异步 + 并行检索）
- ✅ 文档服务（上传处理流水线）

### 安全

- ✅ API Key 认证
- ✅ 请求限流

### 部署

- ✅ 生产级 Docker 配置
- ✅ 多阶段构建
- ✅ 资源限制

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + ECharts + Axios |
| 后端 | FastAPI + Python 3.10 + LangChain |
| 向量数据库 | Milvus v2.3.3 |
| 图数据库 | Neo4j 5.19 |
| Embedding | shibing624/text2vec-base-chinese |
| LLM | MiniMax API (abab6.5s-chat) |
| 缓存 | Redis 7 |
| 部署 | Docker Compose + Nginx |

## 注意事项

1. **API Key** — 需要配置 MiniMax API Key 才能使用问答功能
2. **磁盘空间** — Docker 镜像较大，建议预留 20GB+ 空间
3. **端口占用** — 确保以下端口未被占用：2379, 5003, 5004, 7474, 7687, 9000, 19530, 6379

## License

MIT