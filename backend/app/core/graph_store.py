"""
图谱存储模块
与 Neo4j 交互，存储和查询知识图谱
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jStore:
    """
    Neo4j 图数据库封装
    
    提供以下功能：
    - 初始化图谱 Schema
    - 创建节点
    - 创建关系
    - 查询节点和关系
    - 实体扩展检索
    """
    
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()
    
    def _connect(self):
        """建立与 Neo4j 的连接"""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print(f"✅ Neo4j 连接成功: {self.uri}")
    
    def check_connection(self):
        """检查 Neo4j 连接状态"""
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
    
    def init_schema(self):
        """
        初始化图谱 Schema
        
        创建必要的约束和索引。
        """
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE
            """)
            
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)
            """)
            
            print("✅ Neo4j Schema 初始化完成")
    
    def create_entity(self, name: str, entity_type: str, properties: Dict[str, Any] = None):
        """
        创建实体（节点）
        
        Args:
            name: 实体名称
            entity_type: 实体类型（如 "人物"、"地点"）
            properties: 实体属性
        """
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
        
        with self.driver.session() as session:
            session.run(cypher, **params)
    
    def create_relation(self, from_entity: str, to_entity: str, relation_type: str, properties: Dict[str, Any] = None):
        """
        创建关系（边）
        """
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
            "relation_type": relation_type
        }
        
        with self.driver.session() as session:
            session.run(cypher, **params)
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """
        获取所有节点
        """
        cypher = """
            MATCH (e:Entity)
            RETURN id(e) AS id, e.name AS name, e.type AS type, 
                   PROPERTIES(e) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            nodes = []
            for record in result:
                node = {
                    "id": str(record["id"]),
                    "name": record["name"],
                    "type": record["type"],
                    "properties": {k: v for k, v in record["properties"].items() 
                                  if k not in ["name", "type"]}
                }
                nodes.append(node)
            return nodes
    
    def get_all_relations(self) -> List[Dict[str, Any]]:
        """
        获取所有关系
        """
        cypher = """
            MATCH (a:Entity)-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to,
                   PROPERTIES(r) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            relations = []
            for record in result:
                rel = {
                    "from": record["from"],
                    "to": record["to"],
                    "type": record["type"],
                    "properties": record["properties"] or {}
                }
                relations.append(rel)
            return relations
    
    def search_nodes(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索节点
        """
        cypher = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $keyword OR e.type CONTAINS $keyword
            RETURN id(e) AS id, e.name AS name, e.type AS type
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, keyword=keyword)
            return [{"id": str(r["id"]), "name": r["name"], "type": r["type"]} 
                   for r in result]
    
    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的节点"""
        cypher = """
            MATCH (e:Entity {name: $name})
            RETURN id(e) AS id, e.name AS name, e.type AS type,
                   PROPERTIES(e) AS properties
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, name=name)
            record = result.single()
            if record:
                return {
                    "id": str(record["id"]),
                    "name": record["name"],
                    "type": record["type"],
                    "properties": {k: v for k, v in record["properties"].items()
                                  if k not in ["name", "type"]}
                }
            return None
    
    def get_node_relations(self, name: str) -> List[Dict[str, Any]]:
        """
        获取节点的所有一度关系
        """
        cypher = """
            MATCH (a:Entity {name: $name})-[r]->(b:Entity)
            RETURN a.name AS from, type(r) AS type, b.name AS to
            UNION
            MATCH (a:Entity)-[r]->(b:Entity {name: $name})
            RETURN a.name AS from, type(r) AS type, b.name AS to
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, name=name)
            return [{"from": r["from"], "type": r["type"], "to": r["to"]} 
                   for r in result]
    
    def expand_entities(self, query: str) -> List[Dict[str, Any]]:
        """
        根据查询扩展相关实体
        
        Args:
            query: 用户查询
            
        Returns:
            List[Dict]: 匹配的实体列表
        """
        all_nodes = self.get_all_nodes()
        
        matched = []
        query_lower = query.lower()
        
        for node in all_nodes:
            if (node["name"] in query or 
                query in node["name"] or
                node["name"].lower() in query_lower):
                matched.append(node)
        
        return matched[:10]
    
    def clear_all(self):
        """清空所有节点和关系"""
        cypher = """
            MATCH (n) DETACH DELETE n
        """
        
        with self.driver.session() as session:
            session.run(cypher)
            print("✅ Neo4j 数据已清空")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
