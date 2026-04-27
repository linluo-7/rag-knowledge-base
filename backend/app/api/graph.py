"""
知识图谱 API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.logging import get_logger
from app.schemas import GraphData, EntityData, RelationData
from app.factory import get_graph_store


logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=GraphData)
async def get_graph():
    """
    获取知识图谱的全部数据

    返回所有节点和关系，用于前端可视化
    """
    try:
        graph_store = get_graph_store()

        nodes = graph_store.get_all_nodes()
        relations = graph_store.get_all_relations()

        graph_nodes = [
            EntityData(
                id=n.id,
                name=n.name,
                type=n.type,
                properties=n.properties,
            )
            for n in nodes
        ]

        graph_relations = [
            RelationData(
                from_node=r.from_node,
                to_node=r.to_node,
                type=r.type,
                properties=r.properties,
            )
            for r in relations
        ]

        return GraphData(nodes=graph_nodes, links=graph_relations)

    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_graph(keyword: str):
    """
    搜索图谱中的节点

    根据关键词搜索匹配的节点及其直接关联
    """
    try:
        graph_store = get_graph_store()

        matched_nodes = graph_store.search_nodes(keyword)

        result_nodes = []
        result_relations = []

        for node in matched_nodes:
            node_detail = graph_store.get_node(node.name)
            if node_detail:
                result_nodes.append(node_detail)

            node_relations = graph_store.get_node_relations(node.name)
            result_relations.extend(node_relations)

        unique_nodes = {n.id: n for n in result_nodes}

        return JSONResponse({
            "nodes": list(unique_nodes.values()),
            "relations": result_relations
        })

    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))