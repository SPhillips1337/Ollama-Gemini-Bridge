import os
import asyncio
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from bridge_logic import BridgeLogic
from mcp_client import MCPClient

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("WARNING: No GEMINI_API_KEY found. Bridge will attempt to use local MCP tools for inference.")
    bridge = BridgeLogic(api_key=None)
else:
    bridge = BridgeLogic(api_key=GEMINI_API_KEY)

app = FastAPI(title="Ollama-Gemini Bridge")
mcp_manager = MCPClient()

@app.on_event("startup")
async def startup_event():
    mcp_servers = os.getenv("MCP_SERVERS", "").split(",")
    for server in mcp_servers:
        server = server.strip()
        if server:
            # Connect sequentially during startup to avoid concurrency race conditions in AnyIO
            await mcp_manager.connect_to_server(server)

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_manager.cleanup()

# Simple Bearer Token Auth
def verify_token(authorization: str = Header(None)):
    expected_token = os.getenv("BRIDGE_AUTH_TOKEN")
    if not expected_token:
        return True # Auth disabled if not set
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def load_memories():
    memory_path = ".antigravity/memories"
    if not os.path.exists(memory_path):
        return ""

    memories = ["# LONG TERM MEMORY (Antigravity Agents Prompt Protocol)\n"]
    memories.append("You are operating with Long Term Memory. Use the `commit_memory` tool to extract lessons, patterns, and decisions.\n")

    # Load patterns and lessons
    patterns_file = os.path.join(memory_path, "patterns_and_lessons.md")
    if os.path.exists(patterns_file):
        with open(patterns_file, "r") as f:
            memories.append(f"## Patterns and Lessons\n{f.read()}\n")
    
    # Load architectural decisions
    arch_dir = os.path.join(memory_path, "architectural_decisions")
    if os.path.exists(arch_dir):
        memories.append("## Architectural Decisions\n")
        for f in os.listdir(arch_dir):
            if f.endswith(".md"):
                with open(os.path.join(arch_dir, f), "r") as file:
                    memories.append(f"### {f}\n{file.read()}\n")
                    
    return "\n".join(memories)

@app.post("/api/chat")
async def chat(request: Request, authenticated: bool = Depends(verify_token)):
    body = await request.json()
    model = body.get("model", "gemini-1.5-pro")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    
    # Load LTM and inject into system context
    ltm_content = load_memories()
    if ltm_content:
        # Check if there's already a system message
        system_msg_index = next((i for i, m in enumerate(messages) if m["role"] == "system"), None)
        if system_msg_index is not None:
            messages[system_msg_index]["content"] += f"\n\n{ltm_content}"
        else:
            messages.insert(0, {"role": "system", "content": ltm_content})
    
    if not bridge.client:
        # Keyless mode: Delegate to MCP server
        print("Using MCP-based inference (Gemini CLI)...")
        prompt = messages[-1]["content"] if messages else ""
        
        # Try different tool names and parameter schemas
        inference_tools = [
            ("gemini_prompt", {"prompt": prompt}),
            ("ask-gemini", {"prompt": prompt}),
            ("gemini", {"prompt": prompt}),
            ("prompt", {"text": prompt}),
            ("generate", {"prompt": prompt})
        ]
        
        result = None
        for tool_name, args in inference_tools:
            try:
                print(f"Attempting inference with {tool_name}...")
                result = await mcp_manager.call_tool(tool_name, args)
                if result:
                    print(f"Success with {tool_name}")
                    break
            except Exception as e:
                print(f"Tool {tool_name} failed: {e}")
                continue
        
        content = "Error: No suitable MCP tool found for inference."
        if result:
            if isinstance(result, list):
                content = "\n".join(item.text for item in result if hasattr(item, 'text'))
            else:
                content = str(result)
        
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00.000Z",
            "message": {"role": "assistant", "content": content},
            "done": True
        }

    tools = await mcp_manager.get_tools_for_gemini()
    
    # Initial conversion to Gemini contents
    contents = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role != "system":
            contents.append({"role": bridge._map_role(role), "parts": [{"text": content}]})

    if stream:
        gemini_stream = await bridge.chat_completion(model, messages, tools=tools, stream=True)
        return StreamingResponse(bridge.stream_generator(model, gemini_stream), media_type="application/x-ndjson")
    else:
        # Robust multi-turn tool calling loop
        max_turns = 5
        current_turn = 0
        
        while current_turn < max_turns:
            response = await bridge.chat_completion(model, messages, contents=contents, tools=tools, stream=False)
            candidate = response.candidates[0]
            
            # Check for function calls
            function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
            
            if not function_calls:
                return {
                    "model": model,
                    "created_at": "2024-01-01T00:00:00.000Z",
                    "message": {"role": "assistant", "content": response.text},
                    "done": True
                }
            
            # Add assistant's message with function calls to history
            contents.append(candidate.content)
            
            # Execute tool calls
            tool_parts = []
            for fc in function_calls:
                print(f"Executing tool: {fc.name} with {fc.args}")
                result = await mcp_manager.call_tool(fc.name, fc.args)
                tool_parts.append(bridge.format_tool_response(fc.name, result))
            
            # Add tool results to history
            contents.append({"role": "user", "parts": tool_parts})
            current_turn += 1

        raise HTTPException(status_code=500, detail="Max tool-calling turns reached")

@app.post("/api/generate")
async def generate(request: Request, authenticated: bool = Depends(verify_token)):
    body = await request.json()
    prompt = body.get("prompt", "")
    model = body.get("model", "gemini-1.5-pro")
    stream = body.get("stream", False)
    
    messages = [{"role": "user", "content": prompt}]
    
    if stream:
        gemini_stream = await bridge.chat_completion(model, messages, stream=True)
        return StreamingResponse(bridge.stream_generator(model, gemini_stream), media_type="application/x-ndjson")
    else:
        response = await bridge.chat_completion(model, messages, stream=False)
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00.000Z",
            "response": response.text,
            "done": True
        }

@app.get("/api/tags")
async def tags(authenticated: bool = Depends(verify_token)):
    return {
        "models": [
            {"name": "gemini-1.5-pro", "details": {"family": "gemini"}},
            {"name": "gemini-1.5-flash", "details": {"family": "gemini"}}
        ]
    }

@app.get("/api/version")
async def version():
    return {"version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11434)
