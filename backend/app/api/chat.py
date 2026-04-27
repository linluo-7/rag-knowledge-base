"""
问答 API - 安全版本
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.logging import get_logger
from app.schemas import ChatResponse
from app.service.rag_service import RAGService
from app.auth import require_auth
from app.ratelimit import check_rate_limit
from app.metrics import track_chat
from app.security import sanitize_llm_input, validate_for_embedding
from app.exceptions import ValidationError


logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
@track_chat()
async def chat(
    request: dict,
    current_user: str = Depends(require_auth),
    _rate_limit: None = Depends(check_rate_limit),
):
    """问答接口 - 安全加固版"""
    question = request.get("question", "")
    top_k = request.get("top_k", 5)

    # 验证输入
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # 安全检查 - Embedding 输入
    if not validate_for_embedding(question):
        raise HTTPException(
            status_code=400,
            detail="Input contains suspicious patterns",
        )

    # 安全检查 - Prompt 注入
    question = sanitize_llm_input(question)

    # 长度限制
    if len(question) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Question too long (max 2000 characters)",
        )

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