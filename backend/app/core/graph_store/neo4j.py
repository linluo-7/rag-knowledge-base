"""
Neo4j 图存储实现 - 生产级版本
"""

import asyncio
import threading
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, List, Optional

import aiohttp
from neo4j import GraphDatabase, Driver

from app.config import get_settings
from app.exceptions import GraphStoreConnectionError
from app.logging import get_logger
from app.core.pool import PooledConnection
from app.core.graph_store.base import GraphStore as BaseGraphStore
from app.core.graph_store.base import EntityNode, RelationEdge


logger = get_logger(__name__)


class Neo4jConnectionPool:
    """Neo4j 连接池"""

    _pools: Dict[str, "Neo4jConnectionPool"] = {}
    _lock = threading.Lock()

    def __init__(self, uri: str, user: str, password: str, pool_size: int = 5):
        self.uri = uri
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self._available: List[Driver] = []
        self._lock = threading.Lock()

    def get_driver(self) -> Driver:
        """获取驱动"""
        with self._lock:
            if self._available:
                return self._available.pop()

        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        driver.verify connectivity()
        return driver

    def release_driver(self, driver: Driver) -> None:
        """释放驱动"""
        with self._lock:
            if len(self._available) < self.pool_size:
                try:
                    self._available.append(driver)
                except Exception:
                    driver.close()
            else:
                driver.close()

    @classmethod
    def get_pool(
        cls, uri: str, user: str, password: str, pool_size: int = 5
    ) -> "Neo4jConnectionPool":
        """获取连接池"""
        key = f"{uri}:{user}"
        with cls._lock:
            if key not in cls._pools:
                cls._pools[key] = cls(uri, user, password, pool_size)
            return cls._pools[key]

    @classmethod
    def close_all(cls) -> None:
        """关闭所有连接"""
        with cls._lock:
            for pool in cls._pools.values():
                pool.close()
            cls._pools.clear()

    def close(self) -> None:
        """关闭连接池"""
        with self._lock:
            for driver in self._available:
                try:
                    driver.close()
                except Exception:
                    pass
            self._available.clear()


@contextmanager
def use_neo4j_driver(uri: str = None, user: str = None, password: str = None):
    """同步使用 Neo4j"""
    settings = get_settings()
    uri = uri or settings.NEO4J_URI
    user = user or settings.NEO4J_USER
    password = password or settings.NEO4J_PASSWORD
    pool = Neo4jConnectionPool.get_pool(uri, user, password, settings.NEO4J_POOL_SIZE)

    driver = pool.get_driver()
    try:
        yield driver
    finally:
        pool.release_driver(driver)


class Neo4jGraphStore(BaseGraphStore):
    """Neo4j 图数据库实现 - 生产级

    特性：
    - 连接池管理
    - 线程安全
    - 异步支持
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.pool_size = settings.NEO4J_POOL_SIZE

        self._pool: Optional[Neo4jConnectionPool] = None
        self._connect()

    def _connect(self) -> None:
        """建立连接"""
        try:
            self._pool = Neo4jConnectionPool.get_pool(
                self.uri, self.user, self.password, self.pool_size
            )
            # 验证连接
            with use_neo4j_driver(self.uri, self.user, self.password) as driver:
                with driver.session() as session:
                    result = session.run("RETURN 1 AS test")
                    result.single()
            logger.info(f"Neo4j pool: {self.uri} (size={self.pool_size})")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise GraphStoreConnectionError(
                details={"uri": self.uri, "error": str(e)}
            )

    def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            with use_neo4j_driver(self.uri, self.user, self.password) as driver:
                with driver.session() as session:
                    result = session.run("RETURN 1 AS test")
                    result.single()
            return True
        except Exception:
            return False

    def init_schema(self) -> None:
        """初始化 Schema"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity)
                    REQUIRE n.name IS UNIQUE
                """)
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
        """创建实体"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                props = properties or {}
                props_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
                if props_str:
                    props_str = ", " + props_str

                cypher = f"""
                    MERGE (e:Entity {{name: $name}})
                    SET e.type = $type {props_str}
                    RETURN e
                """
                params = {"name": name, "type": entity_type, **props}
                session.run(cypher, **params)

    def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """创建关系"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                props = properties or {}
                props_list = [f"{k}: '${v}'" for k, v in props.items()]
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
                session.run(cypher, **params)

    def get_all_nodes(self) -> List[EntityNode]:
        """获取所有节点"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity)
                    RETURN id(e) AS id, e.name AS name, e.type AS type,
                           PROPERTIES(e) AS properties
                """)
                nodes = []
                for record in result:
                    node = EntityNode(
                        id=str(record["id"]),
                        name=record["name"],
                        type=record["type"],
                        properties={
                            k: v for k, v in record["properties"].items()
                            if k not in ["name", "type"]
                        },
                    )
                    nodes.append(node)
                return nodes

    def get_all_relations(self) -> List[RelationEdge]:
        """获取所有关系"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (a:Entity)-[r]->(b:Entity)
                    RETURN a.name AS from, type(r) AS type, b.name AS to,
                           PROPERTIES(r) AS properties
                """)
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
        """搜索节点"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.name CONTAINS $keyword OR e.type CONTAINS $keyword
                    RETURN id(e) AS id, e.name AS name, e.type AS type
                """, keyword=keyword)
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
        """获取节点"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {name: $name})
                    RETURN id(e) AS id, e.name AS name, e.type AS type,
                           PROPERTIES(e) AS properties
                """, name=name)
                record = result.single()
                if record:
                    return EntityNode(
                        id=str(record["id"]),
                        name=record["name"],
                        type=record["type"],
                        properties={
                            k: v for k, v in record["properties"].items()
                            if k not in ["name", "type"]
                        },
                    )
                return None

    def get_node_relations(self, name: str) -> List[RelationEdge]:
        """获取节点关系"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (a:Entity {name: $name})-[r]->(b:Entity)
                    RETURN a.name AS from, type(r) AS type, b.name AS to
                    UNION
                    MATCH (a:Entity)-[r]->(b:Entity {name: $name})
                    RETURN a.name AS from, type(r) AS type, b.name AS to
                """, name=name)
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
        """扩展实体"""
        all_nodes = self.get_all_nodes()
        matched = []
        query_lower = query.lower()

        for node in all_nodes:
            if node.name in query or query in node.name or node.name.lower() in query_lower:
                matched.append(node)

        return matched[:10]

    def clear_all(self) -> None:
        """清空数据"""
        with use_neo4j_driver(self.uri, self.user, self.password) as driver:
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("Neo4j data cleared")

    def close(self) -> None:
        """关闭连接"""
        if self._pool:
            self._pool.close()
            logger.info("Neo4j pool closed")