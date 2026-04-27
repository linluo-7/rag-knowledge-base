"""
测试配置
"""

import pytest
from pathlib import Path


# 测试配置
TEST_DIR = Path(__file__).parent
APP_DIR = TEST_DIR.parent / "app"


# Pytest 配置
def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture
def test_settings():
    """测试配置"""
    import os
    from app.config import Settings

    # 测试环境变量
    os.environ["ENV"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["MILVUS_HOST"] = "localhost"
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"

    return Settings()


@pytest.fixture
def mock_milvus(monkeypatch):
    """Mock Milvus"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    monkeypatch.setattr("pymilvus.connections.connect", mock)
    return mock


@pytest.fixture
def mock_neo4j(monkeypatch):
    """Mock Neo4j"""
    from unittest.mock import MagicMock

    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value = mock_session
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    monkeypatch.setattr("neo4j.GraphDatabase.driver", lambda *args, **kwargs: mock_driver)

    return mock_driver


@pytest.fixture
def sample_document():
    """样本文档"""
    return {
        "content": "这是一个测试文档内容。",
        "metadata": {
            "file_id": "test-file-001",
            "filename": "test.txt"
        }
    }


@pytest.fixture
def sample_question():
    """测试问题"""
    return "什么是 RAG？"


@pytest.fixture
def sample_vector():
    """测试向量"""
    import numpy as np

    np.random.seed(42)
    return np.random.randn(768).tolist()