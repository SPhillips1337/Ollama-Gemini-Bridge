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
    
    lines = text.split('\n')
    clean_lines = []
    capture = False
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines or known noise
        if not stripped or "[IDEClient]" in stripped:
            continue
            
        if stripped.startswith('✦'):
            clean_lines.append(stripped.lstrip('✦').strip())
            capture = True
        elif capture:
            if '▀▀▀' in stripped or '▄▄▄' in stripped:
                break
            clean_lines.append(line) # Keep original spacing for captured lines
            
    if not clean_lines:
        # Fallback: filter out obvious infrastructure noise but keep content
        noise_patterns = ['Plan:', 'Signed in', 'ℹ', '▀▀▀', '▄▄▄']
        for line in lines:
            stripped = line.strip()
            if stripped and not any(p in stripped for p in noise_patterns) and "[IDEClient]" not in stripped:
                # Only filter "Gemini CLI" if it looks like a header (short line)
                if "Gemini CLI" in stripped and len(stripped) < 30:
                    continue
                clean_lines.append(stripped)
        
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
