"""
RRF 融合模块
实现向量检索和图谱检索结果的融合排序
"""

from typing import List, Dict, Any


class RRFFusion:
    """
    RRF（倒数排名融合）算法实现
    
    对于每个结果，计算 RRF 得分 = 1 / (k + rank)
    最终得分是所有检索列表中得分的总和。
    """
    
    def __init__(self, k: int = 60):
        self.k = k
    
    def fuse(self, 
             vector_results: List[Dict[str, Any]], 
             graph_results: List[Dict[str, Any]], 
             k: int = None) -> List[Dict[str, Any]]:
        """
        融合向量检索和图谱检索的结果
        
        Args:
            vector_results: Milvus 向量检索结果
            graph_results: Neo4j 图谱检索结果
            k: RRF 参数
            
        Returns:
            List[Dict]: 融合后的结果，按 RRF 得分降序排列
        """
        if k is None:
            k = self.k
        
        if not vector_results:
            return graph_results
        if not graph_results:
            return vector_results
        
        rrf_scores = {}
        
        for rank, result in enumerate(vector_results):
            content = result["content"]
            rrf_score = 1.0 / (k + rank + 1)
            if content in rrf_scores:
                rrf_scores[content]["score"] += rrf_score
                rrf_scores[content]["sources"].append("vector")
            else:
                rrf_scores[content] = {
                    "content": content,
                    "score": rrf_score,
                    "sources": ["vector"],
                    "metadata": result.get("metadata", {})
                }
        
        for rank, result in enumerate(graph_results):
            content = result["content"]
            rrf_score = 1.0 / (k + rank + 1)
            if content in rrf_scores:
                rrf_scores[content]["score"] += rrf_score
                rrf_scores[content]["sources"].append("graph")
            else:
                rrf_scores[content] = {
                    "content": content,
                    "score": rrf_score,
                    "sources": ["graph"],
                    "metadata": result.get("metadata", {})
                }
        
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        return sorted_results
