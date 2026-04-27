# RAG 知识库系统

> 基于 LangChain + Milvus + Neo4j 的 RAG 知识库问答系统

## 版本

**v2.3.0** - 性能优化版本

## 核心特性

| 特性 | 说明 |
|------|------|
| GPU 批处理 | Dynamic Batching 提高吞吐量 |
| 两阶段检索 | Reranking 精排 |
| 混合检索 | BM25 + 向量 |
| 长文档 | Parent Document Retrieval |
| 流式响应 | SSE 实时返回 |

## 快速开始

```bash
# 克隆
git clone https://github.com/linluo-7/rag-knowledge-base.git

# 启动
docker compose -f docker/docker-compose.prod.yml up -d

# 访问
curl http://localhost:5003/docs
```

## 性能对比

| 优化 | 效果 |
|------|------|
| GPU 批处理 | GPU 利用率 30% -> 80% |
| Reranking | 相关性 +20% |
| 混合检索 | 召回率 +15% |
| 长文档 | 支持 10MB+ 文档 |
| 流式 | 首字节 < 1s |

## 项目结构

```
rag-knowledge-base/
├── app/
│   ├── core/
│   │   ├── embedding.py      # GPU 批处理
│   │   ├── rerank.py         # 两阶段检索
│   │   ├── hybrid_search.py  # 混合检索
│   │   ├── longdoc.py        # 长文档
│   │   └── ...
│   ├── api/
│   │   ├── chat.py          # 普通问答
│   │   └── stream.py       # 流式问答
│   └── ...
├── docs/
│   ├── 更新日志.md
│   └── 容量规划.md
└── docker/
```

## License

MIT