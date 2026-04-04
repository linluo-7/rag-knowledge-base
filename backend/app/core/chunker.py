"""
文本分块模块
将长文本分割成较小的重叠 chunk
"""

from typing import List, Dict, Any
import re


class TextChunker:
    """
    文本分块器
    
    使用滑动窗口将文本分割成固定大小的重叠 chunk。
    
    配置：
    - chunk_size: 每个 chunk 的字符数
    - chunk_overlap: chunk 之间的重叠字符数
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source: str = "") -> List[Dict[str, Any]]:
        """
        将文本分割成多个 chunk
        
        Args:
            text: 待分割的文本
            source: 文本来源
            
        Returns:
            List[Dict]: chunk 列表
        """
        if not text or not text.strip():
            return []
        
        text = self._clean_text(text)
        paragraphs = self._split_by_paragraph(text)
        chunks = self._merge_to_chunks(paragraphs, source)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        paragraphs = re.split(r"\n\n+", text)
        
        result = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(p) > self.chunk_size * 2:
                sentences = self._split_by_sentence(p)
                result.extend(sentences)
            else:
                result.append(p)
        
        return result
    
    def _split_by_sentence(self, text: str) -> List[str]:
        sentences = re.split(r"[。！？.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _merge_to_chunks(self, paragraphs: List[str], source: str) -> List[Dict[str, Any]]:
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if para_length > self.chunk_size:
                if current_chunk:
                    chunk_text = self._join_chunk(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": source,
                            "chunk_index": chunk_index,
                            "chunk_size": len(chunk_text)
                        }
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_length = 0
                
                sentences = self._split_by_sentence(para)
                for sentence in sentences:
                    if current_length + len(sentence) <= self.chunk_size:
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
                    else:
                        if current_chunk:
                            chunk_text = self._join_chunk(current_chunk)
                            chunks.append({
                                "content": chunk_text,
                                "metadata": {
                                    "source": source,
                                    "chunk_index": chunk_index,
                                    "chunk_size": len(chunk_text)
                                }
                            })
                            chunk_index += 1
                        
                        if self.chunk_overlap > 0 and current_chunk:
                            overlap_text = self._join_chunk(current_chunk)
                            overlap_sentences = self._split_by_sentence(overlap_text)[-2:]
                            current_chunk = overlap_sentences
                            current_length = sum(len(s) for s in overlap_sentences)
                        else:
                            current_chunk = []
                            current_length = 0
                        
                        current_chunk.append(sentence)
                        current_length += len(sentence) + 1
            
            elif current_length + para_length > self.chunk_size:
                if current_chunk:
                    chunk_text = self._join_chunk(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "source": source,
                            "chunk_index": chunk_index,
                            "chunk_size": len(chunk_text)
                        }
                    })
                    chunk_index += 1
                
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = self._join_chunk(current_chunk)
                    overlap_len = min(len(overlap_text), self.chunk_overlap)
                    overlap_start = len(overlap_text) - overlap_len
                    overlap = overlap_text[overlap_start:]
                    
                    current_chunk = [overlap, para]
                    current_length = len(overlap) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            
            else:
                current_chunk.append(para)
                current_length += para_length + 1
        
        if current_chunk:
            chunk_text = self._join_chunk(current_chunk)
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "source": source,
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text)
                }
            })
        
        return chunks
    
    def _join_chunk(self, parts: List[str]) -> str:
        return " ".join(parts)
