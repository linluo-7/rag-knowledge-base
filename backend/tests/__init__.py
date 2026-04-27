# Tests

测试目录结构：

```
tests/
├── __init__.py
├── conftest.py         # Pytest 配置和 fixtures
├── test_unit.py       # 单元测试
├── test_integration.py # 集成测试
├── test_e2e.py       # 端到端测试 (可选)
└── mocks/            # Mock 对象
```

## 运行测试

```bash
# 所有测试
pytest

# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 跳过集成测试
pytest -m "not integration"

# 带覆盖率
pytest --cov=app --cov-report=html
```

## 测试规范

1. 单元测试: 不依赖外部服务，快速执行
2. 集成测试: 需要 Milvus/Neo4j 服务
3. Mock 外部依赖，确保隔离性