# RAG 知识库系统

> 基于 LangChain + Milvus + Neo4j 的 RAG 知识库问答系统，支持知识图谱构建与双轨检索融合

## 功能特性

- 📄 **文档上传解析** — 支持 Word (.docx)、纯文本 (.txt) 文档上传与内容提取
- 🔍 **向量检索** — Milvus 向量数据库存储 + BGE 中文 Embedding 模型
- 🕸️ **知识图谱** — Neo4j 图数据库存储实体关系，LLM 自动提取
- 💬 **智能问答** — 双轨检索（向量+图谱）+ RRF 融合 + LLM 生成答案
- 📊 **图谱可视化** — ECharts 力导向图展示实体关系网络
- 🐳 **一键部署** — Docker Compose 快速启动全部组件

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
cd backend
cp .env.example .env
# 编辑 .env，填入你的 MiniMax API Key
```

### 3. 启动服务

```bash
# 一键启动全部服务（推荐）
docker compose up -d

# 或分步启动
docker compose up -d milvus neo4j    # 数据库
python -m uvicorn app.main:app --port 5003  # 后端
```

### 4. 访问系统

- 前端界面：http://localhost:5004
- 后端 API：http://localhost:5003
- Neo4j Browser：http://localhost:7474

## 项目结构

```
rag-knowledge-base/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   │   ├── chat.py      # 问答接口
│   │   │   ├── graph.py     # 图谱接口
│   │   │   └── upload.py    # 上传接口
│   │   ├── core/            # 核心模块
│   │   │   ├── document.py  # 文档解析
│   │   │   ├── chunker.py   # 文本分块
│   │   │   ├── embedding.py # BGE Embedding
│   │   │   ├── vector_store.py  # Milvus
│   │   │   ├── graph_store.py   # Neo4j
│   │   │   ├── fusion.py    # RRF 融合
│   │   │   └── llm.py       # MiniMax LLM
│   │   ├── schemas/          # Pydantic 模型
│   │   └── main.py          # FastAPI 入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   └── api/             # API 调用封装
│   └── Dockerfile
├── docs/                     # 开发文档（10篇）
│   ├── 01-项目介绍.md
│   ├── 07-后端开发.md
│   └── 10-Docker部署.md
└── docker-compose.yml        # 一键部署配置
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/upload/` | 上传文档 | 解析文档，存入向量库和图谱 |
| `POST /api/chat/` | 问答 | 输入问题，返回答案和相关文档 |
| `GET /api/graph/` | 获取图谱 | 返回所有实体和关系 |
| `GET /api/graph/search` | 搜索图谱 | 按关键词搜索相关实体 |
| `GET /health` | 健康检查 | 检查 Milvus 和 Neo4j 状态 |

## 开发文档

详细的开发指南见 [`docs/`](docs/) 目录：

- [01-项目介绍.md](docs/01-项目介绍.md) — 系统架构、数据流程
- [02-环境检查.md](docs/02-环境检查.md) — Docker、Git 检查
- [03-Milvus部署.md](docs/03-Milvus部署.md) — 向量数据库部署
- [04-Neo4j安装.md](docs/04-Neo4j安装.md) — 图数据库安装
- [05-Python环境.md](docs/05-Python环境.md) — Conda 环境配置
- [06-项目初始化.md](docs/06-项目初始化.md) — 项目结构、API 路由
- [07-后端开发.md](docs/07-后端开发.md) — 7个核心模块详解
- [08-前端开发.md](docs/08-前端开发.md) — React 页面、ECharts 图谱
- [09-前后端联调.md](docs/09-前后端联调.md) — 联调测试
- [10-Docker部署.md](docs/10-Docker部署.md) — 一键部署

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + ECharts + Axios |
| 后端 | FastAPI + Python 3.10 + LangChain |
| 向量数据库 | Milvus v2.3.3 |
| 图数据库 | Neo4j 5.19 |
| Embedding | shibing624/text2vec-base-chinese |
| LLM | MiniMax API (abab6.5s-chat) |
| 部署 | Docker Compose + Nginx |

## 注意事项

1. **API Key** — 需要配置 MiniMax API Key 才能使用问答功能
2. **磁盘空间** — Docker 镜像较大，建议预留 20GB+ 空间
3. **端口占用** — 确保以下端口未被占用：2379, 5003, 5004, 7474, 7687, 9000, 19530

## License

MIT
