# RAG 知识库系统

> 基于 LangChain + Milvus + Neo4j 的 RAG 知识库问答系统，支持知识图谱构建与双轨检索融合

## 版本

**v2.1.0** - 生产级加固版本

## 功能特性

- 📄 **文档上传解析** — 支持 Word (.docx)、纯文本 (.txt) 文档上传与内容提取
- 🔍 **向量检索** — Milvus 向量数据库存储 + BGE 中文 Embedding 模型
- 🕸️ **知识图谱** — Neo4j 图数据库存储实体关系，LLM 自动提取
- 💬 **智能问答** — 双轨检索（向量+图谱）+ RRF 融合 + LLM 生成答案
- 📊 **图谱可视化** — ECharts 力导向图展示实体关系网络
- 🐳 **一键部署** — Docker Compose 快速启动全部组件
- 🔒 **认证限流** — API Key 认证 + Redis 分布式限流
- 📈 **监控告警** — Prometheus 监控 + 健康检查
- 🛡️ **安全加固** — 渗透防护 + Prompt 注入防御

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
│  │ 安全检查│  │ 重试策略│  │ 连接复用│  │ 熔断器  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ RRF 融合  │  │ 多级缓存 │  │ 限流   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Milvus  │    │   Neo4j  │    │ MiniMax  │
    │ 长连接池 │    │ 连接池   │    │ API Key │ │← 智能轮换
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
# 生产级部署（推荐）
docker compose -f docker/docker-compose.prod.yml up -d
```

### 4. 访问系统

- 后端 API：http://localhost:5003
- API 文档：http://localhost:5003/docs
- 指标端点：http://localhost:5003/metrics
- Neo4j Browser：http://localhost:7474

## v2.1.0 改进

| 维度 | 解决方案 | 作用 |
|------|---------|------|
| 连接管理 | 长连接 + 健康检查 | 避免重复创建，短路恢复 |
| 重试策略 | 指数退避 + 熔断 | 防雪崩，防抖动 |
| 限流 | Redis 滑动窗口 | 分布式精确限流 |
| 缓存 | 多级 + 版本控制 | 一致性保证 |
| 安全 | 渗透防护 | 文件/Prompt/SSRF |

### 认证调用

```bash
# 带 API Key 调用
curl -X POST http://localhost:5003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"question": "什么是 RAG?"}'
```

### 查看监控

```bash
# Prometheus 指标
curl http://localhost:5003/metrics

# 健康检查
curl http://localhost:5003/health
curl http://localhost:5003/health/deep
```

## 项目结构

```
rag-knowledge-base/
├── app/                         # FastAPI 后端
│   ├── main.py                  # 入口 + 中间件
│   ├── config.py              # Pydantic 配置
│   ├── dependencies.py       # FastAPI 依赖注入
│   ├── factory.py           # 单例工厂
│   ├── exceptions.py         # 分级异常
│   ├── logging.py           # 结构化日志
│   ├── auth.py            # API Key 认证
│   ├── ratelimit.py       # 分布式限流
│   ├── metrics.py         # Prometheus 监控
│   ├── security.py        # 渗透防护
│   ├── sanitize.py       # 敏感信息脱敏
│   │
│   ├── core/                   # 基础设施
│   │   ├── vector_store/      # Milvus + 连接池
│   │   ├── graph_store/     # Neo4j + 连接池
│   │   ├── llm/          # MiniMax + 重试
│   │   ├── cache.py       # 多级缓存
│   │   ├── retry.py      # 熔断器
│   │   └── pool.py       # 连接管理
│   │
│   ├── service/              # 业务层
│   ├── api/               # 入口层
│   └── schemas/           # 数据模型
│
├── docker/                    # Docker 配置
└── docs/                   # 文档
    └── 更新日志.md          # 版本变更
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + ECharts |
| 后端 | FastAPI + Python 3.10 |
| 向量数据库 | Milvus v2.3.3 |
| 图数据库 | Neo4j 5.19 |
| Embedding | BGE |
| LLM | MiniMax API |
| 缓存 | Redis 7 |
| 监控 | Prometheus |
| 部署 | Docker Compose |

## License

MIT