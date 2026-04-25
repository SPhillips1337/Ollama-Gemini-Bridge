# Ollama-Gemini Bridge

A high-performance, Ollama and OpenAI-compatible HTTP bridge written in Python (FastAPI). This bridge allows you to use Gemini models with any client (Open WebUI, AnythingLLM, VS Code extensions, etc.) while leveraging your local **Gemini CLI OAuth session** or a direct API key.

## 🚀 Key Features

- **Dual Protocol Support**: Full implementation of Ollama (`/api/*`) and OpenAI (`/v1/*`) endpoints.
- **Ultra-Low Latency Caching**: 
    - **Tool Caching**: In-memory storage of MCP tool definitions to bypass JSON-RPC discovery overhead.
    - **Inference Caching**: Remembers successful tool-mapping for instant model routing.
    - **LTM Caching**: Zero-disk I/O memory retrieval using an in-memory project context index.
- **Reliability Watchdog**: Background process that monitors and auto-heals crashed MCP server connections.
- **Public Discovery**: Open endpoints for server verification in tools like Hermes.
- **Dual Inference Modes**:
    - **Keyless (CLI) Mode**: Uses your local `gemini` CLI session via a non-interactive wrapper.
    - **Direct API Mode**: Uses `GEMINI_API_KEY` for multi-turn agentic workflows.
- **Long Term Memory (LTM)**: Context-aware keyword matching for persistent project insights.
- **Streaming Support**: Real-time "Thought" logging and final text streaming.

## 🛠️ Quick Start

### 1. Installation & Configuration
The easiest way to set up the bridge is using the interactive installation script:

```bash
# Clone the repo (if you haven't already)
# git clone <repo_url>
# cd ollama-gemini-bridge

# Run the interactive installer
./install.sh
```

The script will:
- Check for system dependencies (Python, Node.js, Gemini CLI).
- Create a Python virtual environment.
- Install all necessary packages.
- **Interactively** configure your `.env` file (choosing between Keyless CLI or Direct API modes).

### 2. Running the Bridge
Once installed, start the bridge with:
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 11434
```

### Health Check
```bash
# Check if bridge is running
curl -s http://localhost:11434/api/version

# Test with auth (replace token with your BRIDGE_AUTH_TOKEN)
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secure_bearer_token_here" \
  -d '{"model":"gemini-1.5-flash","prompt":"Hello"}'

## 🧠 Smart Long Term Memory (LTM)

The bridge uses a **Context-Aware RAG** approach for LTM:
- **Intelligent Loading**: Only injects memories relevant to the user's latest prompt.
- **Persistence**: Save architectural decisions and lessons learned via the `commit_memory` tool.
- **Speed**: Memories are indexed in RAM for instant context injection.

## 🔌 Connecting Clients

### Ollama Clients (Open WebUI / AnythingLLM)
- **Base URL**: `http://localhost:11434`
- **Model**: `gemini-1.5-pro`

### OpenAI-Compatible Clients (Hermes / VS Code)
- **Base URL**: `http://localhost:11434/v1`
- **Auth**: Set API Key to your `BRIDGE_AUTH_TOKEN`.

## 🤖 Agent Orchestration
Refine the bridge's logic using the built-in CrewAI agents:
```bash
python crew_orchestrator.py
```
