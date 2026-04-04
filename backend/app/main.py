"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from app.config import API_HOST, API_PORT
from app.api.router import api_router


def init_databases():
    """在后台线程初始化数据库连接"""
    def _init():
        try:
            from app.core.vector_store import MilvusStore
            milvus_store = MilvusStore()
            milvus_store.init_collection()
            print("✅ Milvus 连接成功")
        except Exception as e:
            print(f"⚠️ Milvus 连接失败: {e}")
        
        try:
            from app.core.graph_store import Neo4jStore
            neo4j_store = Neo4jStore()
            neo4j_store.init_schema()
            print("✅ Neo4j 连接成功")
        except Exception as e:
            print(f"⚠️ Neo4j 连接失败: {e}")
    
    thread = threading.Thread(target=_init, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 RAG 知识库系统启动中...")
    init_databases()
    yield
    print("👋 RAG 知识库系统关闭")


app = FastAPI(
    title="RAG 知识库问答系统",
    description="基于 LangChain + Milvus + Neo4j 的 RAG 系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api", tags=["API"])


@app.get("/")
async def root():
    return {"message": "RAG 知识库问答系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    from datetime import datetime
    
    milvus_status = "unknown"
    neo4j_status = "unknown"
    
    try:
        from app.core.vector_store import MilvusStore
        milvus_store = MilvusStore()
        milvus_store.check_connection()
        milvus_status = "healthy"
    except:
        milvus_status = "unhealthy"
    
    try:
        from app.core.graph_store import Neo4jStore
        neo4j_store = Neo4jStore()
        neo4j_store.check_connection()
        neo4j_status = "healthy"
    except:
        neo4j_status = "unhealthy"
    
    return {
        "status": "ok",
        "milvus": milvus_status,
        "neo4j": neo4j_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
