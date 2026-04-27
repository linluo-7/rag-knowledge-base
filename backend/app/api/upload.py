"""
文档上传 API
"""

import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging import get_logger
from app.schemas import UploadResponse
from app.service.document_service import DocumentService


logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档并处理

    流程：
    1. 验证文件
    2. 解析文档内容
    3. 文本分块
    4. 生成 Embedding
    5. 存储到 Milvus
    6. 提取实体关系存储到 Neo4j
    """
    settings = get_settings()

    # 读取文件内容
    file_content = await file.read()

    # 验证文件大小
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(file_content)} bytes",
        )

    # 验证文件扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}",
        )

    try:
        service = DocumentService()
        result = await service.process_document(file_content, file.filename)

        return UploadResponse(
            file_id=result["file_id"],
            filename=result["filename"],
            status=result["status"],
            message=f"文档上传成功！解析了 {result['chunks_count']} 个文本块，"
            f"提取了 {result['entities_count']} 个实体和 "
            f"{result['relations_count']} 个关系",
            chunks_count=result["chunks_count"],
            entities_count=result["entities_count"],
            relations_count=result["relations_count"],
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))