import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self._exit_stack = AsyncExitStack()

    async def connect_to_server(self, command_str: str):
        try:
            # Handle potential CWD prefix: [CWD:/path/to/dir] command args...
            cwd = None
            if command_str.startswith("[CWD:"):
                end_idx = command_str.find("]")
                cwd = command_str[5:end_idx]
                command_str = command_str[end_idx+1:].strip()

            parts = command_str.split()
            command = parts[0]
            args = parts[1:]
            
            server_params = StdioServerParameters(
                command=command, 
                args=args,
                env={**os.environ, "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "dummy")}
            )
            if cwd:
                server_params.cwd = cwd
            
            # Use AsyncExitStack to manage the lifecycle of both the transport and session
            read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            self.sessions.append(session)
            print(f"Successfully connected to MCP server: {command_str}")
        except Exception as e:
            print(f"Failed to connect to MCP server ({command_str}): {e}")

    async def get_tools_for_gemini(self) -> List[Dict[str, Any]]:
        gemini_tools = []
        for session in self.sessions:
            try:
                tools_resp = await session.list_tools()
                for tool in tools_resp.tools:
                    gemini_tools.append({
                        "function_declarations": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema
                            }
                        ]
                    })
            except Exception as e:
                print(f"Error fetching tools from a session: {e}")
        return gemini_tools

    async def call_tool(self, name: str, arguments: dict):
        for session in self.sessions:
            try:
                # Check if tool exists in this session first
                tools_resp = await session.list_tools()
                if not any(t.name == name for t in tools_resp.tools):
                    continue

                result = await session.call_tool(name, arguments)
                return result.content
            except Exception as e:
                print(f"Error calling tool {name} in a session: {e}")
                continue
        return None

    async def cleanup(self):
        await self._exit_stack.aclose()
