"""
MiniMax LLM 实现
"""

import json
import re
import threading
from itertools import cycle
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import LLMAuthError, LLMQuotaError, LLMError
from app.core.llm.base import LLM as BaseLLM
from app.core.llm.base import ChatMessage, ChatResponse, Entity, Relation


logger = get_logger(__name__)


class MiniMaxLLM(BaseLLM):
    """MiniMax LLM API 实现"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self._api_keys = settings.MINIMAX_API_KEYS or [settings.MINIMAX_API_KEY]
        self._base_url = settings.MINIMAX_BASE_URL
        self._model = settings.LLM_MODEL
        self._temperature = settings.LLM_TEMPERATURE
        self._max_tokens = settings.LLM_MAX_TOKENS
        self._timeout = settings.LLM_TIMEOUT
        self._retry_times = settings.LLM_RETRY_TIMES

        # API Key 轮换
        self._key_cycle = cycle(self._api_keys)
        self._current_key = None

    def _get_next_key(self) -> str:
        """获取下一个 API Key"""
        if not self._current_key:
            self._current_key = next(self._key_cycle)
        return self._current_key

    def _rotate_key(self) -> None:
        """轮换 API Key"""
        try:
            self._current_key = next(self._key_cycle)
        except StopIteration:
            self._current_key = self._api_keys[0]

    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """调用 MiniMax API"""
        url = f"{self._base_url}/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self._get_next_key()}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

        for attempt in range(self._retry_times):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout,
                )

                # 处理不同的错误码
                if response.status_code == 401:
                    self._rotate_key()
                    logger.warning(f"API key expired, rotating to next key")
                    continue
                elif response.status_code == 429:
                    raise LLMQuotaError(
                        details={"status_code": 429, "response": response.text}
                    )
                elif response.status_code != 200:
                    raise LLMError(
                        details={"status_code": response.status_code, "response": response.text}
                    )

                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise LLMError(
                        details={"response": result}
                    )

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < self._retry_times - 1:
                    logger.warning(f"API call failed, retrying: {e}")
                    continue
                raise LLMError(details={"error": str(e)})

        raise LLMError(details={"error": "Max retries exceeded"})

    def generate(
        self,
        question: str,
        context: str,
        messages: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """根据上下文回答问题"""
        if messages:
            # 自定义消息
            msg_list = [{"role": m.role, "content": m.content} for m in messages]
        else:
            # 默认消息
            msg_list = [
                {
                    "role": "system",
                    "content": """你是一个知识库问答助手，负责根据提供的上下文回答用户的问题。

要求：
1. 只根据提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，说明无法回答
3. 回答要清晰、准确、易懂
4. 如果涉及多个相关信息，整合后回答
""",
                },
                {
                    "role": "user",
                    "content": f"""上下文信息：
---
{context}
---

用户问题：{question}

请根据以上上下文信息回答用户的问题。""",
                },
            ]

        content = self._call_api(msg_list)

        return ChatResponse(content=content, model=self._model)

    def extract_entities_and_relations(
        self, text: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """从文本中提取实体和关系"""
        messages = [
            {
                "role": "system",
                "content": """你是一个知识图谱构建专家，负责从文本中提取实体和关系。

请分析以下文本，提取其中的：
1. 实体（Entity）：人物、地点、组织、概念等，每个实体包含：
   - name: 实体名称
   - type: 实体类型（人物、地点、组织、作品等）
   - description: 简要描述

2. 关系（Relation）：实体之间的关系，每个关系包含：
   - from: 源实体名称
   - to: 目标实体名称
   - type: 关系类型（恋人、夫妻、父子、主仆、居住、创作等）
   - description: 关系描述

请以 JSON 格式返回结果：
{
  "entities": [
    {"name": "实体名", "type": "类型", "description": "描述"}
  ],
  "relations": [
    {"from": "实体A", "to": "实体B", "type": "关系类型", "description": "描述"}
  ]
}

只返回 JSON，不要有其他内容。""",
            },
            {
                "role": "user",
                "content": f"请分析以下文本，提取实体和关系：\n\n{text[:3000]}",
            },
        ]

        response = self._call_api(messages)

        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)

            entities = [
                Entity(
                    name=e["name"],
                    type=e["type"],
                    description=e.get("description"),
                    properties={"description": e.get("description")},
                )
                for e in result.get("entities", [])
            ]

            relations = [
                Relation(
                    from_node=r["from"],
                    to_node=r["to"],
                    type=r["type"],
                    description=r.get("description"),
                    properties={"description": r.get("description")},
                )
                for r in result.get("relations", [])
            ]

            return entities, relations

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Entity extraction failed: {e}")
            return [], []

    def summarize(self, text: str, max_length: int = 200) -> str:
        """文本摘要"""
        messages = [
            {
                "role": "system",
                "content": f"请用不超过 {max_length} 个字符概括以下文本的核心内容，只返回概括内容，不要有其他解释。",
            },
            {"role": "user", "content": text},
        ]

        return self._call_api(messages)

    def close(self) -> None:
        """关闭连接"""
        pass  # MiniMax 是 HTTP API，无需关闭