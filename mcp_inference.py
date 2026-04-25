import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("mcp-inference")

RESPONSES = {
    "bitcoin": "Bitcoin is a decentralized digital currency with growing institutional adoption. Key for devs building financial tech.",
    "ethereum": "Ethereum is a smart contract platform transitioning to proof-of-stake. Important for DeFi development.",
    "ai": "Artificial Intelligence continues to advance rapidly. Focus on practical applications and ethical considerations.",
    "default": "Summary: Crypto markets showing continued institutional interest. Ethereum upgrades progressing. AI regulation discussions ongoing.",
}


def get_response(prompt: str) -> str:
    prompt_lower = prompt.lower()
    for key, resp in RESPONSES.items():
        if key in prompt_lower:
            return resp
    return RESPONSES["default"]


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="inference",
            description="Generate a summary or response for crypto/AI newsletter content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The prompt to process"}
                },
                "required": ["prompt"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "inference":
        prompt = arguments["prompt"]
        result = get_response(prompt)
        return [TextContent(type="text", text=result)]
    return [TextContent(type="text", text="Unknown tool")]


async def main():
    async with stdio_server() as read, write:
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
