"""
LLM 模块
调用 MiniMax API 进行文本生成和实体关系提取
"""

import json
import re
from typing import List, Dict, Any, Tuple
import requests
from app.config import MINIMAX_API_KEY, MINIMAX_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class MiniMaxLLM:
    """
    MiniMax LLM API 封装
    
    提供以下功能：
    - 文本生成（对话）
    - 实体关系提取
    """
    
    def __init__(
        self, 
        api_key: str = MINIMAX_API_KEY,
        base_url: str = MINIMAX_BASE_URL,
        model: str = LLM_MODEL,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """
        调用 MiniMax API
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            
        Returns:
            str: API 返回的文本内容
        """
        url = f"{self.base_url}/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"API 返回格式异常: {result}")
    
    def generate(self, question: str, context: str) -> str:
        """
        根据上下文回答问题
        
        Args:
            question: 用户问题
            context: 检索到的上下文
            
        Returns:
            str: 生成的回答
        """
        messages = [
            {
                "role": "system",
                "content": """你是一个知识库问答助手，负责根据提供的上下文回答用户的问题。

要求：
1. 只根据提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，说明无法回答
3. 回答要清晰、准确、易懂
4. 如果涉及多个相关信息，整合后回答
"""
            },
            {
                "role": "user",
                "content": f"""上下文信息：
---
{context}
---

用户问题：{question}

请根据以上上下文信息回答用户的问题。
"""
            }
        ]
        
        return self._call_api(messages)
    
    def extract_entities_and_relations(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从文本中提取实体和关系
        
        使用 LLM 分析文本，提取其中的实体（如人物、地点、组织等）
        和关系（如恋人、夫妻、主仆等）。
        
        Args:
            text: 待分析的文本
            
        Returns:
            Tuple[List[Dict], List[Dict]]: 
                - entities: 实体列表，每个包含 name, type, properties
                - relations: 关系列表，每个包含 from, to, type, properties
        """
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

只返回 JSON，不要有其他内容。
"""
            },
            {
                "role": "user",
                "content": f"请分析以下文本，提取实体和关系：\n\n{text[:3000]}"
            }
        ]
        
        response = self._call_api(messages)
        
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
            
            entities = result.get("entities", [])
            relations = result.get("relations", [])
            
            return entities, relations
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ 实体关系提取失败: {e}")
            print(f"原始响应: {response}")
            return [], []
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """
        文本摘要
        
        Args:
            text: 待摘要的文本
            max_length: 最大长度（字符数）
            
        Returns:
            str: 摘要文本
        """
        messages = [
            {
                "role": "system",
                "content": f"请用不超过 {max_length} 个字符概括以下文本的核心内容，只返回概括内容，不要有其他解释。"
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        return self._call_api(messages)


# ============ 使用示例 ============
if __name__ == "__main__":
    # 注意：需要先设置 MINIMAX_API_KEY 环境变量
    # import os
    # os.environ["MINIMAX_API_KEY"] = "your_api_key"
    
    llm = MiniMaxLLM()
    
    # 测试问答
    # answer = llm.generate(
    #     question="贾宝玉和林黛玉是什么关系？",
    #     context="贾宝玉是《红楼梦》的男主角，林黛玉是女主角，两人从小一起长大，感情深厚，是恋人关系。"
    # )
    # print(f"回答: {answer}")
    
    # 测试实体关系提取
    test_text = """
    贾宝玉是《红楼梦》的男主角，他出身于贾府，是贾母的孙子。贾宝玉与林黛玉从小一起长大，感情深厚，两人是恋人关系。

    林黛玉是贾宝玉的表妹，她聪明伶俐，多愁善感。林黛玉最终因病去世，令人惋惜。

    薛宝钗是贾宝玉的表姐，后成为贾宝玉的妻子。她性格温柔贤惠。
    """
    
    entities, relations = llm.extract_entities_and_relations(test_text)
    
    print("提取的实体:")
    for e in entities:
        print(f"  - {e['name']} ({e['type']}): {e.get('description', '')}")
    
    print("\n提取的关系:")
    for r in relations:
        print(f"  - {r['from']} --[{r['type']}]--> {r['to']}")
