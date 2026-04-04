"""
文档上传 API
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.models import UploadResponse
from app.config import UPLOAD_DIR
from app.core.document import DocumentParser
from app.core.chunker import TextChunker
from app.core.embedding import EmbeddingModel
from app.core.vector_store import MilvusStore
from app.core.graph_store import Neo4jStore
from app.core.llm import MiniMaxLLM

router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档并处理
    
    流程：
    1. 保存上传文件
    2. 解析文档内容
    3. 文本分块
    4. 生成 Embedding
    5. 存储到 Milvus
    6. 提取实体关系存储到 Neo4j
    """
    file_id = str(uuid.uuid4())
    
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
    
    try:
        parser = DocumentParser()
        text = parser.parse(str(file_path))
        
        chunker = TextChunker()
        chunks = chunker.chunk(text)
        
        embedding_model = EmbeddingModel()
        milvus_store = MilvusStore()
        neo4j_store = Neo4jStore()
        llm = MiniMaxLLM()
        
        vectors = embedding_model.embed_documents(chunks)
        milvus_store.insert(chunks, vectors, {"file_id": file_id, "filename": file.filename})
        
        entities, relations = llm.extract_entities_and_relations(text)
        
        for entity in entities:
            neo4j_store.create_entity(entity["name"], entity["type"], entity.get("properties", {}))
        for relation in relations:
            neo4j_store.create_relation(
                relation["from"],
                relation["to"],
                relation["type"],
                relation.get("properties", {})
            )
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            status="success",
            message=f"文档上传成功！解析了 {len(chunks)} 个文本块，提取了 {len(entities)} 个实体和 {len(relations)} 个关系"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}")
