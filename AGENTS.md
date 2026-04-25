# Agentic Capabilities & Reasoning

The Ollama-Gemini Bridge transforms Gemini into a robust, context-intelligent autonomous agent with a transparent reasoning process.

## 🧠 Advanced Reasoning & UX

### 1. Transparent "Thought" Streaming
Unlike standard bridges that hide tool-calling overhead, this bridge streams its thinking process to the client in real-time.
- **UX feedback**: You will see messages like `> 🛠️ Calling tool: commit_memory...` in your UI before the final answer arrives.
- **Transparency**: This allows you to verify that the agent is correctly utilizing its tools (Memory, Search, Reasoning) during the interaction.

### 2. Context-Aware LTM (Simple RAG)
To prevent context window saturation, the bridge implements a keyword-based retrieval system for **Long Term Memory**.
- **Keyword Matching**: The bridge tokenizes your prompt and cross-references it against the memory index.
- **Memory Injection**: Only the most relevant architectural decisions and codebase insights are injected into the system prompt.
- **Performance**: All memory content is cached in memory for zero-latency injection.

### 3. Reliability Watchdog
Agentic workflows often run for long periods. To ensure stability:
- **Periodic Health Checks**: Every 60 seconds, the bridge pings all connected MCP servers.
- **Self-Healing**: If a server (like a local Node.js MCP instance) crashes, the watchdog automatically re-spawns it and refreshes the tool cache without interrupting your active sessions.

## 🛠️ Tool Calling & Multi-turn Execution

The bridge manages the complexity of Gemini's `function_call` schema automatically:

1. **Detection**: Recognizes when the model requires external data.
2. **Local Routing**: Uses the **In-memory Tool Cache** to instantly find the correct MCP server.
3. **Execution**: Performs the JSON-RPC call and captures the result.
4. **Recursive Loop**: Feeds results back to Gemini (up to 5 times) to allow for complex, multi-step reasoning.

## 🚀 Keyless vs. Direct API Workflows

| Feature | Keyless (CLI) | Direct (API) |
|---------|---------------|--------------|
| **Multi-turn Loop** | Handled by CLI | Handled by Bridge |
| **Streaming** | Simulated | Native |
| **Auth** | OAuth session | API Key |
| **Stability** | High | Ultra-High |

## 🚀 Optimization Tip
To maximize reasoning speed, ensure your most frequently used MCP servers are listed first in your `.env`. The bridge will prioritize them during the tool discovery phase.
