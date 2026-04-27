# RAG 知识库系统

> 基于 LangChain + Milvus + Neo4j 的 RAG 知识库问答系统，支持知识图谱构建与双轨检索融合

## 版本

**v2.2.0** - 工程完善版本

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
- 🧪 **测试覆盖** — 单元测试 + 集成测试
- 📋 **容量规划** — 资源计算 + 成本预估
- 🔄 **灾备方案** — 备份 + 恢复 + 高可用

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

## v2.2.0 改进

| 功能 | 说明 |
|------|------|
| 容量规划 | 硬件配置 + 成本预估 |
| 测试覆盖 | 单元测试 + 集成测试 |
| 灾备方案 | 备份 + 恢复流程 |
| CI/CD | GitHub Actions 流水线 |

## 项目结构

```
rag-knowledge-base/
├── app/                         # FastAPI 后端
│   ├── main.py                  # 入口
│   ├── config.py               # 配置
│   ├── dependencies.py          # 依赖注入
│   ├── auth.py               # 认证
│   ├── ratelimit.py         # 限流
│   ├── metrics.py            # 监控
│   ├── security.py          # 安全
│   ├── core/                # 核心模块
│   │   ├── vector_store/     # 向量存储
│   │   ├── graph_store/     # 图存储
│   │   ├── llm/           # LLM
│   │   ├── cache.py        # 缓存
│   │   └── retry.py        # 重试
│   └── service/             # 业务
├── backend/tests/              # 测试
├── docker/                   # Docker
├── docs/                    # 文档
│   ├── 更新日志.md          # 变更日志
│   ├── 容量规划.md        # 容量规划
│   └── 灾备方案.md        # 灾备方案
└── .github/workflows/      # CI/CD
```

## 文档

- [更新日志](docs/更新日志.md) - 版本变更
- [容量规划](docs/容量规划.md) - 资源计算
- [灾备方案](docs/灾备方案.md) - 灾难恢复

## License

MIT