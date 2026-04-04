"""
全局配置文件
所有配置项从此处读取，支持从环境变量覆盖
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j123456")

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
EMBEDDING_DEVICE = "cpu"

CHUNK_SIZE = 256
CHUNK_OVERLAP = 64

RRF_K = 60
TOP_K = 5

LLM_MODEL = "abab6.5s-chat"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1024

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MILVUS_COLLECTION = "documents"
MILVUS_DIM = 768
