"""
问答 API
"""

from fastapi import APIRouter, HTTPException
from app.schemas.models import ChatRequest, ChatResponse, SourceDocument
from app.core.embedding import EmbeddingModel
from app.core.vector_store import MilvusStore
from app.core.graph_store import Neo4jStore
from app.core.fusion import RRFFusion
from app.core.llm import MiniMaxLLM

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    问答接口
    
    流程：
    1. 问题 Embedding
    2. Milvus 向量检索
    3. Neo4j 图谱检索（实体扩展）
    4. RRF 融合
    5. LLM 生成答案
    """
    try:
        embedding_model = EmbeddingModel()
        milvus_store = MilvusStore()
        neo4j_store = Neo4jStore()
        llm = MiniMaxLLM()
        fusion = RRFFusion()
        
        query_vector = embedding_model.embed_query(request.question)
        
        milvus_results = milvus_store.search(query_vector, top_k=request.top_k)
        
        graph_entities = neo4j_store.expand_entities(request.question)
        neo4j_results = []
        if graph_entities:
            for entity in graph_entities:
                related_texts = milvus_store.search_by_entity(entity["name"], top_k=2)
                neo4j_results.extend(related_texts)
        
        fused_results = fusion.fuse(milvus_results, neo4j_results, k=60)
        
        context = "\n\n".join([r["content"] for r in fused_results[:3]])
        
        answer = llm.generate(request.question, context)
        
        sources = [
            SourceDocument(
                content=r["content"],
                score=r["score"],
                metadata=r.get("metadata", {})
            )
            for r in fused_results[:request.top_k]
        ]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            graph_entities=graph_entities
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {e}")
