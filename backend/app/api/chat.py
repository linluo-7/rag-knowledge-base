"""
问答 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.logging import get_logger
from app.schemas import ChatResponse
from app.service.rag_service import RAGService


logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """问答请求"""
    question: str
    top_k: int = 5


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """问答接口"""
    try:
        rag_service = RAGService()
        result = await rag_service.chat(
            question=request.question,
            top_k=request.top_k,
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            graph_entities=result["graph_entities"],
            latent_ms=result["latency_ms"],
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))