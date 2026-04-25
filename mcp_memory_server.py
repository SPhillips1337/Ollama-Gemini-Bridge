import os
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

server = Server("mcp-memory")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="commit_memory",
            description="Commit an insight, architectural decision, or coding pattern to long-term memory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["codebase_insights", "architectural_decisions", "patterns"],
                        "description": "The category of memory."
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the memory (used as filename for insights/decisions)."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to store."
                    }
                },
                "required": ["category", "title", "content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "commit_memory":
        category = arguments["category"]
        title = arguments["title"]
        content = arguments["content"]
        
        base_path = ".antigravity/memories"
        
        if category == "patterns":
            file_path = os.path.join(base_path, "patterns_and_lessons.md")
            with open(file_path, "a") as f:
                f.write(f"\n### {title}\n{content}\n")
        else:
            dir_path = os.path.join(base_path, category)
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, f"{title.lower().replace(' ', '_')}.md")
            with open(file_path, "w") as f:
                f.write(f"# {title}\n\n{content}\n")
        
        return [TextContent(type="text", text=f"Successfully committed to {category} memory: {title}")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
