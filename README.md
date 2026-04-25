# Ollama-Gemini Bridge

A high-performance, Ollama and OpenAI-compatible HTTP bridge written in Python (FastAPI). This bridge allows you to use Gemini models with any client (Open WebUI, AnythingLLM, VS Code extensions, etc.) while leveraging your local **Gemini CLI OAuth session** or a direct API key.

## 🚀 Key Features

- **Dual Protocol Support**:
    - **Ollama API**: Implements `/api/chat`, `/api/generate`, and `/api/tags`.
    - **OpenAI API**: Implements `/v1/chat/completions` and `/v1/models`.
- **Public Discovery**: Discovery endpoints (`/v1/models`, `/api/tags`) are public, allowing tools like Hermes to verify the bridge without initial authentication.
- **Dual Inference Modes**:
    - **Keyless (CLI) Mode**: Uses your local `gemini` CLI OAuth session via a robust non-interactive wrapper. No API key required in `.env`.
    - **Direct API Mode**: Uses `GEMINI_API_KEY` for high-performance, multi-turn agentic workflows.
- **Agentic MCP Integration**: Dynamically maps local Model Context Protocol (MCP) tools to Gemini.
- **Long Term Memory (LTM)**: Implements the [Antigravity Agents Prompt Protocol](https://github.com/SPhillips1337/AntigravityAgentsPromptProtocol) for persistent codebase insights and architectural decisions.
- **Streaming Support**: Real-time NDJSON (Ollama) and SSE (OpenAI) streaming for "typing" effects.
- **Security**: Built-in Bearer Token authentication configurable via `.env`.

## 🛠️ Quick Start

### 1. Installation
```bash
# Clone the repo and install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file from the template:
```env
# Optional: Leave as placeholder to use Keyless (CLI) mode
GEMINI_API_KEY=your_gemini_api_key_here

BRIDGE_AUTH_TOKEN=your_secure_bearer_token_here

# Register MCP servers (CWD prefix supported for local paths)
MCP_SERVERS=npx -y @modelcontextprotocol/server-everything,python3 gemini_cli_mcp.py,python3 mcp_memory_server.py
```

### 3. Running the Bridge
```bash
uvicorn main:app --host 0.0.0.0 --port 11434
```

## 🧠 Long Term Memory (LTM)

The bridge uses a local `.antigravity/memories/` directory to store and retrieve project context:
- **Architectural Decisions**: Injected into the system prompt to guide the model's design choices.
- **Patterns & Lessons**: Learned from previous sessions to prevent recurring mistakes.
- **Echo Tool**: The model can call the `commit_memory` tool to autonomously save new insights.

## 🔌 Connecting Clients

### Ollama Clients (Open WebUI / AnythingLLM)
1. **Ollama Base URL**: Set to `http://localhost:11434`.
2. **Auth Header**: Add `Authorization: Bearer <your_token>` if `BRIDGE_AUTH_TOKEN` is set.
3. **Model**: Select `gemini-1.5-pro`.

### OpenAI-Compatible Clients
1. **Base URL**: Set to `http://localhost:11434/v1`.
2. **API Key**: Set to your `BRIDGE_AUTH_TOKEN`.
3. **Model**: Select `gemini-1.5-pro`.

## 📝 Troubleshooting
- **CLI Mode Errors**: Ensure `gemini --version` works in your terminal and you are logged in via `gemini login`.
- **CWD Errors**: If an MCP server fails to find a file, use the `[CWD:/path/to/dir]` prefix in your `MCP_SERVERS` list.
- **Streaming**: Ensure your client supports the protocol format (NDJSON for Ollama, SSE for OpenAI).

## 🤖 Agent Orchestration
This project was built with **CrewAI**. You can refine the bridge's logic by running:
```bash
python crew_orchestrator.py
```
