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

import re

def clean_output(text: str) -> str:
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Remove the banner and status messages (look for the large block of ▀ or status lines)
    # The actual content usually comes after a line of ▄▄▄... and before another block
    # Or just look for the first line starting with ✦
    lines = text.split('\n')
    clean_lines = []
    capture = False
    for line in lines:
        if line.strip().startswith('✦'):
            clean_lines.append(line.strip().lstrip('✦').strip())
            capture = True
        elif capture:
            if '▀▀▀' in line or '▄▄▄' in line:
                break
            clean_lines.append(line)
            
    if not clean_lines:
        # Fallback: if we didn't find the ✦ marker, just return the whole thing minus obvious banner lines
        return "\n".join([l for line in lines if (l := line.strip()) and not any(x in l for x in ['Gemini CLI', 'Plan:', 'Signed in', 'ℹ'])])
        
    return "\n".join(clean_lines).strip()

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "gemini_prompt":
        prompt = arguments["prompt"]
        try:
            # Call the gemini CLI in non-interactive mode
            process = await asyncio.create_subprocess_exec(
                "gemini", "--prompt", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = clean_output(stdout.decode())
                return [TextContent(type="text", text=output)]
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
