# Agentic Capabilities & Reasoning

The Ollama-Gemini Bridge is designed to transform Gemini from a standard LLM into an autonomous agent capable of tool execution, structured reasoning, and long-term context retention.

## 🧠 Reasoning Architecture

### 1. Sequential Thinking
By registering the `sequential-thinking` MCP server, Gemini gain access to a structured "thought buffer." 
- **Internal Loop**: Before responding to a complex request, the model can use tools to break down the problem into steps.
- **Chain of Thought**: This mimics advanced reasoning models (like o1) by forcing the model to validate its assumptions at each step.

### 2. Context Gravity (LTM)
The bridge implements the **Antigravity Agents Prompt Protocol**. This prevents "context gravity"—the tendency for an agent to lose focus or re-learn basic project rules over time.
- **Bootstrap Phase**: On every `/api/chat` request, the bridge reads `.antigravity/memories/` and injects them into the System Message.
- **Knowledge Ratcheting**: The model uses the `commit_memory` tool to "ratchet" its knowledge forward, ensuring that a lesson learned in one session is available in all future sessions.

## 🛠️ Tool Calling & Execution

The bridge handles tool calling differently depending on the operating mode:

### Direct API Mode (Multi-turn Agent)
In this mode, the bridge manages a recursive **Multi-turn Loop**:
1. **Gemini**: Generates a `function_call` request.
2. **Bridge**: Intercepts the request and identifies the correct local MCP server.
3. **Execution**: The bridge executes the tool via STDIO and captures the result.
4. **Feedback**: The bridge sends the tool output back to Gemini in a `function_response` part.
5. **Iteration**: Gemini continues this loop (up to 5 times) until it has gathered all necessary data for its final answer.

### Keyless (CLI) Mode (Single-turn Wrapper)
In this mode, tool calling is delegated to the **Gemini CLI's internal MCP engine**. 
- The bridge sends the prompt to the CLI.
- The CLI uses its own configured MCP servers (defined in `~/.gemini/settings.json`) to execute tools.
- The bridge returns the final textual output.

## 🤖 Specialized Agents (CrewAI)

The bridge logic itself is refined by a crew of specialized agents defined in `crew_orchestrator.py`:

| Agent | Responsibility |
|-------|----------------|
| **API Designer** | Ensures the FastAPI endpoints strictly adhere to the Ollama spec. |
| **MCP Integrator** | Manages JSON-RPC transport and dynamic tool mapping. |
| **Documentation Agent** | Maintains architectural clarity and usage guides. |

## 🚀 How to Enable Full Reasoning
To maximize the agentic performance of this bridge:
1. Use **Direct API Mode** by setting `GEMINI_API_KEY`.
2. Add reasoning tools to your `.env`:
   ```env
   MCP_SERVERS=npx -y @modelcontextprotocol/server-sequential-thinking, ...
   ```
3. Prompt the agent to save its work:
   *"Summarize our design decision and commit it to memory."*
