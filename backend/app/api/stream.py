"""
流式响应
Server-Sent Events (SSE) 用于长文本生成
"""

import asyncio
import json
from typing import AsyncGenerator, List

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


# SSE 格式
async def sse_send(event: str, data: str) -> str:
    """生成 SSE 格式"""
    return f"event: {event}\ndata: {data}\n\n"


async def sse_data(data: str) -> str:
    """生成 SSE data"""
    return f"data: {data}\n\n"


class LLMStreamer:
    """LLM 流式响应

    将 LLM 生成的内容流式返回
    """

    def __init__(self, llm):
        self.llm = llm

    async def stream_generate(
        self,
        question: str,
        context: str,
    ) -> AsyncGenerator[str, None]:
        """流式生成

        注意：MiniMax API 原生不支持流式
        这里模拟流式：生成完整后分段发送
        """
        try:
            # 1. 生成完整回答
            response = self.llm.generate(question, context)

            # 2. 分段发送（模拟流式）
            content = response.content
            chunk_size = 50  # 每次发送 50 字符

            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]

                yield await sse_data(json.dumps({
                    "type": "content",
                    "chunk": chunk,
                    "done": False,
                }))

                # 模拟流式延迟
                await asyncio.sleep(0.05)

            # 3. 发送完成信号
            yield await sse_data(json.dumps({
                "type": "done",
                "content": content,
            }))

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield await sse_data(json.dumps({
                "type": "error",
                "error": str(e),
            }))


@router.post("/stream")
async def stream_chat(request: Request):
    """流式问答接口

    使用：
    ```javascript
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        body: JSON.stringify({question: '...'})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        console.log(decoder.decode(value));
    }
    ```
    """
    from app.service.rag_service import RAGService

    # 获取请求体
    body = await request.json()
    question = body.get("question", "")

    if not question:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Question required")

    try:
        # 生成流
        async def generate():
            service = RAGService()
            result = await service.chat(question)

            # 发送来源
            yield await sse_data(json.dumps({
                "type": "sources",
                "data": result["sources"],
            }))

            # 流式发送回答
            content = result["answer"]
            chunk_size = 30

            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield await sse_data(json.dumps({
                    "type": "content",
                    "chunk": chunk,
                }))
                await asyncio.sleep(0.03)

            # 完成
            yield await sse_data(json.dumps({
                "type": "done",
                "latency_ms": result["latency_ms"],
            }))

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        error_msg = f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        return StreamingResponse(
            iter([error_msg]),
            media_type="text/event-stream",
        )


# 前端使用示例
FRONTEND_EXAMPLE = '''
// 前端调用示例
async function streamChat(question) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let answer = '';

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'content') {
          answer += data.chunk;
          console.log(data.chunk); // 实时显示
        }
      }
    }
  }

  return answer;
}
'''