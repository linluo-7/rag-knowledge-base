"""
长文档处理
Parent Document Retrieval
- 父文档（完整内容）
- 子文档（分块，用于检索）
- 检索时召回子文档，引用父文档
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class ParentDocumentChunker:
    """父子文档分块器

    保留父子关系用于长文档检索
    """

    def __init__(
        self,
        parent_size: int = 2000,  # 父文档大小
        child_size: int = 256,    # 子文档大小
        overlap: int = 64,         # 重叠
    ):
        self.parent_size = parent_size
        self.child_size = child_size
        self.overlap = overlap

    def chunk(
        self,
        text: str,
        document_id: str = None,
        metadata: Optional[Dict] = None,
    ) -> Tuple[List[Dict], Dict]:
        """
        分块处理

        Returns:
            (子文档列表, 父文档)
        """
        document_id = document_id or str(uuid.uuid4())
        metadata = metadata or {}

        # 1. 分割父文档（较大块）
        parents = self._split_into_parents(text)

        # 2. 每个父文档分割成子文档
        children = []
        parent_id_map = {}  # 子文档 -> 父文档 ID

        for i, parent in enumerate(parents):
            parent_id = f"{document_id}_parent_{i}"

            # 父文档内容
            parent_doc = {
                "id": parent_id,
                "content": parent,
                "type": "parent",
                "metadata": metadata,
            }

            # 分割子文档
            child_chunks = self._split_text(parent)
            for j, child_content in enumerate(child_chunks):
                child_id = f"{document_id}_child_{i}_{j}"

                child_doc = {
                    "id": child_id,
                    "content": child_content,
                    "type": "child",
                    "metadata": {
                        **metadata,
                        "parent_id": parent_id,
                        "child_index": j,
                    },
                }

                children.append(child_doc)
                parent_id_map[child_id] = parent_id

        return children, {
            "id": document_id,
            "type": "parent",
            "content": text,
            "metadata": metadata,
        }

    def _split_into_parents(self, text: str) -> List[str]:
        """分割成父文档"""
        parents = []
        start = 0

        while start < len(text):
            end = min(start + self.parent_size, len(text))

            # 尽量在句子边界切
            if end < len(text):
                # 向前找标点
                for punct in "。！？.!?":
                    pos = text.rfind(punct, start, end)
                    if pos > start:
                        end = pos + 1
                        break

            parents.append(text[start:end])
            start = end - self.overlap  # 有重叠

        return parents if parents else [text]

    def _split_text(self, text: str) -> List[str]:
        """分割成子文档"""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.child_size, len(text))

            if end < len(text):
                # 向前找标点
                for punct in "。！？.!?\n":
                    pos = text.rfind(punct, start, end)
                    if pos > start:
                        end = pos + 1
                        break

            chunks.append(text[start:end].strip())
            start = end - self.overlap

        return [c for c in chunks if c.strip()]


class LongDocumentRetrieval:
    """长文档检索

    检索时返回父子文档的完整上下文
    """

    def __init__(self):
        self.chunker = ParentDocumentChunker()

    def process_document(
        self,
        text: str,
        embedding_model,
        vector_store,
        document_id: str = None,
        metadata: Optional[Dict] = None,
    ) -> dict:
        """处理长文档"""
        # 1. 分块
        children, parent = self.chunker.chunk(text, document_id, metadata)

        # 2. 向量化子文档
        child_contents = [c["content"] for c in children]
        vectors = embedding_model.embed_documents(child_contents)

        # 3. 存入向量库
        from app.core.vector_store.base import VectorDocument

        docs = [
            VectorDocument(
                content=c["content"],
                vector=v,
                metadata=c["metadata"],
            )
            for c, v in zip(children, vectors)
        ]

        vector_store.insert(docs)

        logger.info(f"Processed long document: {len(children)} children, parent stored")

        return {
            "parent_id": parent["id"],
            "children_count": len(children),
        }

    def retrieve(
        self,
        query: str,
        vector_store,
        embedding_model,
        top_k: int = 5,
    ) -> List[dict]:
        """检索并返回完整上下文"""
        # 1. 检索子文档
        query_vector = embedding_model.embed_query(query)
        child_results = vector_store.search(query_vector, top_k=top_k)

        if not child_results:
            return []

        # 2. 提取父文档 ID
        parent_ids = set()
        parent_contents = {}

        # 3. 查找父文档内容
        # 简化：子文档内容 + 附近子文档内容拼接
        results = []
        for result in child_results:
            metadata = result.metadata
            parent_id = metadata.get("parent_id")

            # 获取同一父文档下的所有子文档
            all_by_parent = [
                r for r in child_results
                if r.metadata.get("parent_id") == parent_id
            ]

            # 拼接完整上下文
            combined = "\n\n".join([
                r.content for r in sorted(all_by_parent, key=lambda x: x.metadata.get("child_index", 0))
            ])

            results.append({
                "content": combined,
                "score": result.score,
                "metadata": metadata,
                "is_long": len(combined) > 500,
            })

        return results