"""
Neo4j 图存储实现
"""

import threading
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import GraphStoreError, GraphStoreConnectionError
from app.core.graph_store.base import GraphStore as BaseGraphStore
from app.core.graph_store.base import EntityNode, RelationEdge


logger = get_logger(__name__)


class Neo4jGraphStore(BaseGraphStore):
    """Neo4j 图数据库实现"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD

        self._driver = None
        self._connect()

    def _connect(self) -> None:
        """建立与 Neo4j 的连接"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            logger.info(f"Neo4j connected: {self.uri}")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise GraphStoreConnectionError(
                details={"uri": self.uri, "error": str(e)}
            )

    def check_connection(self) -> bool:
        """检查 Neo4j 连接状态"""
        try:
            with self._driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            return True
        except Exception:
            return False

    def init_schema(self) -> None:
        """初始化图谱 Schema"""
        with self._driver.session() as session:
            # 创建唯一约束
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity)
                REQUIRE n.name IS UNIQUE
            """)

            # 创建索引
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)
            """)

            logger.info("Neo4j schema initialized")

    def create_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """创建实体节点"""
        properties = properties or {}

        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        if props_str:
            props_str = ", " + props_str

        cypher = f"""
            MERGE (e:Entity {{name: $name}})
            SET e.type = $type {props_str}
            RETURN e
        """

        params = {"name": name, "type": entity_type, **properties}

        with self._driver.session() as session:
            session.run(cypher, **params)

    def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """创建关系边"""
        properties = properties or {}

        props_list = []
        for k, v in properties.items():
            props_list.append(f"{k}: '${v}'")
        props_str = ", " + ", ".join(props_list) if props_list else ""

        cypher = f"""
            MATCH (a:Entity {{name: $from_entity}})
            MATCH (b:Entity {{name: $to_entity}})
            MERGE (a)-[r:{relation_type} {{name: $relation_type{props_str}}}]->(b)
            RETURN r
        """

        params = {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "relation_type": relation_type,
        }

        with self._driver.session() as session:
            session.run(cypher, **params)

    def get_all_nodes(self) -> List[EntityNode]:
        """获取所有节点"""
        cypher = """
            MATCH (e:Entity)
            RETURN id(e) AS id, e.name AS name, e.type AS type,
                   PROPERTIES(e) AS properties
        """

        with self._driver.session() as session:
            result = session.run(cypher)
            nodes = []
            for record in result:
                node = EntityNode(
                    id=str(record["id"]),
                    name=record["name"],
                    type=record["type"],
                    properties={
                        k: v
                        for k, v in record["properties"].items()
                        if k not in ["name", "type"]
                    },
                )
                nodes.append(node)
            return nodes

    def get_all_relations(self) -> List[RelationEdge]:
        """获取所有关系"""
        cypher = """
            MATCH (a:Entity)-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to,
                   PROPERTIES(r) AS properties
        """

        with self._driver.session() as session:
            result = session.run(cypher)
            relations = []
            for record in result:
                rel = RelationEdge(
                    from_node=record["from"],
                    to_node=record["to"],
                    type=record["type"],
                    properties=record["properties"] or {},
                )
                relations.append(rel)
            return relations

    def search_nodes(self, keyword: str) -> List[EntityNode]:
        """根据关键词搜索节点"""
        cypher = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $keyword OR e.type CONTAINS $keyword
            RETURN id(e) AS id, e.name AS name, e.type AS type
        """

        with self._driver.session() as session:
            result = session.run(cypher, keyword=keyword)
            return [
                EntityNode(
                    id=str(r["id"]),
                    name=r["name"],
                    type=r["type"],
                    properties={},
                )
                for r in result
            ]

    def get_node(self, name: str) -> Optional[EntityNode]:
        """获取指定名称的节点"""
        cypher = """
            MATCH (e:Entity {name: $name})
            RETURN id(e) AS id, e.name AS name, e.type AS type,
                   PROPERTIES(e) AS properties
        """

        with self._driver.session() as session:
            result = session.run(cypher, name=name)
            record = result.single()
            if record:
                return EntityNode(
                    id=str(record["id"]),
                    name=record["name"],
                    type=record["type"],
                    properties={
                        k: v
                        for k, v in record["properties"].items()
                        if k not in ["name", "type"]
                    },
                )
            return None

    def get_node_relations(self, name: str) -> List[RelationEdge]:
        """获取节点的所有一度关系"""
        cypher = """
            MATCH (a:Entity {name: $name})-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to
            UNION
            MATCH (a:Entity)-[r]->(b:Entity {name: $name})
            RETURN a.name AS from, type(r) AS type, b.name AS to
        """

        with self._driver.session() as session:
            result = session.run(cypher, name=name)
            return [
                RelationEdge(
                    from_node=r["from"],
                    to_node=r["to"],
                    type=r["type"],
                    properties={},
                )
                for r in result
            ]

    def expand_entities(self, query: str) -> List[EntityNode]:
        """根据查询扩展相关实体"""
        all_nodes = self.get_all_nodes()

        matched = []
        query_lower = query.lower()

        for node in all_nodes:
            if (
                node.name in query
                or query in node.name
                or node.name.lower() in query_lower
            ):
                matched.append(node)

        return matched[:10]

    def clear_all(self) -> None:
        """清空所有节点和关系"""
        cypher = """
            MATCH (n) DETACH DELETE n
        """

        with self._driver.session() as session:
            session.run(cypher)
            logger.info("Neo4j data cleared")

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")