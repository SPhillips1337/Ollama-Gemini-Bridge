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
        self._server_commands: Dict[ClientSession, str] = {}
        self._tool_cache: Dict[ClientSession, List[Any]] = {}
        self._exit_stack = AsyncExitStack()

    async def connect_to_server(self, command_str: str):
        try:
            # Handle potential CWD prefix: [CWD:/path/to/dir] command args...
            cwd = None
            orig_command_str = command_str
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
            
            # Cache tools immediately on connection
            tools_resp = await session.list_tools()
            self._tool_cache[session] = tools_resp.tools
            
            self.sessions.append(session)
            self._server_commands[session] = orig_command_str
            print(f"Successfully connected to MCP server and cached tools: {command_str}")
        except Exception as e:
            print(f"Failed to connect to MCP server ({command_str}): {e}")

    async def health_check(self):
        dead_sessions = []
        for session in self.sessions:
            try:
                # Ping the server and refresh tool cache
                tools_resp = await asyncio.wait_for(session.list_tools(), timeout=5.0)
                self._tool_cache[session] = tools_resp.tools
            except Exception as e:
                print(f"MCP server health check failed for {self._server_commands.get(session, 'unknown')}: {e}")
                dead_sessions.append(session)
        
        for session in dead_sessions:
            cmd = self._server_commands.pop(session, None)
            self._tool_cache.pop(session, None)
            if session in self.sessions:
                self.sessions.remove(session)
            if cmd:
                print(f"Attempting to reconnect to {cmd}...")
                await self.connect_to_server(cmd)

    async def get_tools_for_gemini(self) -> List[Dict[str, Any]]:
        gemini_tools = []
        for session in self.sessions:
            tools = self._tool_cache.get(session, [])
            for tool in tools:
                gemini_tools.append({
                    "function_declarations": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    ]
                })
        return gemini_tools

    async def call_tool(self, name: str, arguments: dict):
        for session in self.sessions:
            try:
                # Check if tool exists in cache first (instant local check)
                tools = self._tool_cache.get(session, [])
                if not any(t.name == name for t in tools):
                    continue

                result = await session.call_tool(name, arguments)
                return result.content
            except Exception as e:
                print(f"Error calling tool {name} in a session: {e}")
                continue
        return None

    async def cleanup(self):
        await self._exit_stack.aclose()
