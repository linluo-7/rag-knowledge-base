"""
文档服务层
封装文档处理的核心业务逻辑
"""

import uuid
import shutil
from pathlib import Path
from typing import List

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import DocumentParseError, UnsupportedFormatError
from app.core.vector_store.base import VectorDocument


logger = get_logger(__name__)


class DocumentService:
    """文档服务"""

    def __init__(self):
        settings = get_settings()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.max_upload_size = settings.MAX_UPLOAD_SIZE

    async def process_document(
        self, file_content: bytes, filename: str
    ) -> dict:
        """
        处理上传的文档

        流程：
        1. 验证文件
        2. 保存文件
        3. 解析文档
        4. 文本分块
        5. 向量化
        6. 存入 Milvus
        7. 提取实体关系存入 Neo4j
        """
        # ===== 1. 验证文件 =====
        self._validate_file(filename, len(file_content))

        file_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{file_id}_{filename}"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        try:
            # ===== 2. 保存文件 =====
            file_path.write_bytes(file_content)
            logger.info(f"File saved: {file_path}")

            # ===== 3. 解析文档 =====
            parser = self._get_document_parser()
            text = parser.parse(str(file_path))

            # ===== 4. 文本分块 =====
            chunker = self._get_chunker()
            chunks = chunker.chunk(text)

            # ===== 5. 向量化 =====
            embedding_model = self._get_embedding_model()
            texts = [chunk["content"] for chunk in chunks]
            vectors = embedding_model.embed_documents(texts)

            # ===== 6. 存入 Milvus =====
            vector_docs = [
                VectorDocument(
                    content=chunk["content"],
                    vector=vector,
                    metadata={"file_id": file_id, "filename": filename},
                )
                for chunk, vector in zip(chunks, vectors)
            ]

            vector_store = self._get_vector_store()
            vector_store.insert(vector_docs)
            logger.info(f"Inserted {len(vector_docs)} vectors to Milvus")

            # ===== 7. 提取实体关系 =====
            entities, relations = self._extract_entities_relations(text)

            graph_store = self._get_graph_store()
            for entity in entities:
                graph_store.create_entity(
                    name=entity.name,
                    entity_type=entity.type,
                    properties=entity.properties,
                )

            for relation in relations:
                graph_store.create_relation(
                    from_entity=relation.from_node,
                    to_entity=relation.to_node,
                    relation_type=relation.type,
                    properties=relation.properties,
                )

            logger.info(
                f"Extracted {len(entities)} entities and "
                f"{len(relations)} relations"
            )

            return {
                "file_id": file_id,
                "filename": filename,
                "chunks_count": len(chunks),
                "entities_count": len(entities),
                "relations_count": len(relations),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            # 清理文件
            if file_path.exists():
                file_path.unlink()
            raise DocumentParseError(
                message=f"Document processing failed: {e}",
                details={"filename": filename},
            )

    def _validate_file(self, filename: str, file_size: int) -> None:
        """验证文件"""
        # 检查大小
        if file_size > self.max_upload_size:
            raise UnsupportedFormatError(f"File too large: {file_size} bytes")

        # 检查扩展名
        ext = Path(filename).suffix.lower()
        settings = get_settings()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise UnsupportedFormatError(ext)

    def _get_document_parser(self):
        from app.factory import Factory

        return Factory.get_document_parser()

    def _get_chunker(self):
        from app.factory import Factory

        return Factory.get_chunker()

    def _get_embedding_model(self):
        from app.factory import Factory

        return Factory.get_embedding_model()

    def _get_vector_store(self):
        from app.factory import get_vector_store

        return get_vector_store()

    def _get_graph_store(self):
        from app.factory import get_graph_store

        return get_graph_store()

    def _extract_entities_relations(self, text):
        llm = self._get_llm()
        return llm.extract_entities_and_relations(text)

    def _get_llm(self):
        from app.factory import get_llm

        return get_llm()