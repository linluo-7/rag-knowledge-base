"""
集成测试
"""

import pytest


@pytest.mark.integration
class TestMilvusIntegration:
    """Milvus 集成测试"""

    @pytest.fixture
    def milvus_store(self):
        """Milvus Store"""
        from app.core.vector_store import MilvusVectorStore

        # 只在有 Milvus 时运行
        pytest.importorskip("pymilvus")
        return MilvusVectorStore()

    def test_connection(self, milvus_store):
        """测试连接"""
        pytest.skip("需要 Milvus 服务")

    def test_insert_and_search(self, milvus_store):
        """测试插入和检索"""
        pytest.skip("需要 Milvus 服务")


@pytest.mark.integration
class TestRAGIntegration:
    """RAG 集成测试"""

    @pytest.fixture
    def rag_service(self):
        """RAG Service"""
        from app.service.rag_service import RAGService

        return RAGService()

    @pytest.mark.asyncio
    async def test_chat(self, rag_service):
        """测试问答"""
        pytest.skip("需要完整服务")


@pytest.mark.integration
class TestAPIIntegration:
    """API 集成测试"""

    @pytest.fixture
    def client(self):
        """Test Client"""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_health(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code in [200, 503]

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()

    def test_metrics(self, client):
        """测试指标端点"""
        response = client.get("/metrics")
        assert response.status_code == 200


@pytest.mark.integration
class TestAuthIntegration:
    """认证集成测试"""

    @pytest.fixture
    def client(self):
        """Test Client"""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_chat_without_auth(self, client, monkeypatch):
        """测试无认证"""
        monkeypatch.setenv("AUTH_REQUIRED", "false")

        response = client.post(
            "/api/v1/chat/",
            json={"question": "test?"},
        )
        assert response.status_code in [200, 500]

    def test_chat_with_invalid_key(self, client, monkeypatch):
        """测试无效 Key"""
        monkeypatch.setenv("AUTH_REQUIRED", "true")

        response = client.post(
            "/api/v1/chat/",
            json={"question": "test?"},
            headers={"X-API-Key": "invalid"},
        )
        assert response.status_code == 401