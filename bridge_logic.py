import json
import time
from typing import List, Dict, Any, AsyncGenerator
from google import genai
from google.genai import types

class BridgeLogic:
    def __init__(self, api_key: str = None):
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def _map_role(self, role: str) -> str:
        if role == "user":
            return "user"
        if role == "assistant":
            return "model"
        if role == "system":
            return "user"
        return "user"

    async def chat_completion(self, model: str, messages: List[Dict[str, str]], contents: List[types.Content] = None, tools: List[Dict] = None, stream: bool = False):
        if not self.client:
            raise ValueError("Direct Gemini API access requires an API key. Please check your MCP configuration.")
        
        if contents is None:
            contents = []
            system_instruction = None
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "system":
                    system_instruction = content
                else:
                    contents.append(types.Content(role=self._map_role(role), parts=[types.Part.from_text(text=content)]))
        else:
            # If contents are passed directly (for multi-turn), use them
            system_instruction = None # Usually doesn't change in turns

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.7,
        )

        if stream:
            return await self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config
            )
        else:
            return await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )

    def format_tool_response(self, tool_name: str, result: Any) -> types.Part:
        return types.Part.from_function_response(
            name=tool_name,
            response={"result": result}
        )

    async def openai_stream_generator(self, model: str, gemini_stream):
        import uuid
        chat_id = str(uuid.uuid4())
        async for chunk in gemini_stream:
            text = chunk.text or ""
            openai_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": text},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(openai_chunk)}\n\n"
        
        yield "data: [DONE]\n\n"
