"""
知识图谱 API
"""

from fastapi import APIRouter, HTTPException
from app.schemas.models import GraphResponse, GraphData, GraphNode, GraphRelation
from app.core.graph_store import Neo4jStore

router = APIRouter()


@router.get("/", response_model=GraphResponse)
async def get_graph():
    """
    获取知识图谱的全部数据
    
    返回所有节点和关系，用于前端可视化
    """
    try:
        neo4j_store = Neo4jStore()
        
        nodes = neo4j_store.get_all_nodes()
        relations = neo4j_store.get_all_relations()
        
        graph_nodes = [
            GraphNode(
                id=n["id"],
                name=n["name"],
                type=n["type"],
                properties=n.get("properties", {})
            )
            for n in nodes
        ]
        
        graph_relations = [
            GraphRelation(
                source=r["from"],
                target=r["to"],
                type=r["type"],
                properties=r.get("properties", {})
            )
            for r in relations
        ]
        
        return GraphResponse(
            data=GraphData(nodes=graph_nodes, relations=graph_relations),
            total_nodes=len(graph_nodes),
            total_relations=len(graph_relations)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱查询失败: {e}")


@router.get("/search")
async def search_graph(keyword: str):
    """
    搜索图谱中的节点
    
    根据关键词搜索匹配的节点及其直接关联
    """
    try:
        neo4j_store = Neo4jStore()
        
        matched_nodes = neo4j_store.search_nodes(keyword)
        
        result_nodes = []
        result_relations = []
        
        for node in matched_nodes:
            node_detail = neo4j_store.get_node(node["name"])
            if node_detail:
                result_nodes.append(node_detail)
            
            node_relations = neo4j_store.get_node_relations(node["name"])
            result_relations.extend(node_relations)
        
        unique_nodes = {n["id"]: n for n in result_nodes}
        
        return {
            "nodes": list(unique_nodes.values()),
            "relations": result_relations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱搜索失败: {e}")
