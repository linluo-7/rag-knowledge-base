"""
问答 API - 生产级版本
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.logging import get_logger
from app.schemas import ChatResponse
from app.service.rag_service import RAGService
from app.auth import require_auth
from app.ratelimit import check_rate_limit
from app.metrics import track_chat


logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
@track_chat()
async def chat(
    request: dict,
    current_user: str = Depends(require_auth),
    _rate_limit: None = Depends(check_rate_limit),
):
    """问答接口

    流程：
    1. 认证检查（通过 require_auth）
    2. 限流检查（通过 check_rate_limit）
    3. RAG 处理
    """
    question = request.get("question", "")
    top_k = request.get("top_k", 5)

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        service = RAGService()
        result = await service.chat(
            question=question,
            user_id=current_user if current_user != "anonymous" else None,
            top_k=top_k,
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            graph_entities=result["graph_entities"],
            latent_ms=result["latency_ms"],
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat processing failed")