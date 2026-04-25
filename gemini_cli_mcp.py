import os
import json
import subprocess
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("gemini-cli-wrapper")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="gemini_prompt",
            description="Run a prompt through the Gemini CLI (uses local OAuth session).",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to Gemini."
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "gemini_prompt":
        prompt = arguments["prompt"]
        try:
            # Call the gemini CLI directly
            process = await asyncio.create_subprocess_exec(
                "gemini", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return [TextContent(type="text", text=stdout.decode().strip())]
            else:
                return [TextContent(type="text", text=f"Error: {stderr.decode().strip()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Exception: {str(e)}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
