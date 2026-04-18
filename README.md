# MCP Rick and Morty Demo

A simple example project to understand **MCP (Model Context Protocol)** using:

- an **MCP server** in Python
- an **LLM client** in Python
- the public **Rick and Morty API**
- optional **native tool-calling style**
- optional **fallback JSON-style tool invocation**

## What this project does

This demo shows how an LLM-powered client can talk to an MCP server.

The MCP server:

- fetches characters from the Rick and Morty API
- exposes a tool called `find_rick_and_morty_character`
- returns structured character data

The client:

- starts the MCP server over stdio
- reads available tools using `list_tools()`
- converts MCP tool definitions into LLM tool schema
- asks the LLM a question
- if the LLM requests a tool, calls the MCP server tool
- sends the tool result back to the LLM
- prints the final answer

---

## Files

### `server.py`
Python MCP server.

Responsibilities:

- connect to Rick and Morty API
- fetch all character pages
- search characters by name
- expose the MCP tool:
  - `find_rick_and_morty_character`

### `client.py`
Python MCP client.

Responsibilities:

- start local MCP server
- initialize MCP session
- read tools from server
- convert MCP tool schemas into LLM tool definitions
- ask the LLM
- call MCP tool when needed
- print final answer

### `run.ps1`
PowerShell helper script to:

- create virtual environment
- install dependencies
- run the client

---

## Architecture

```text
User Question
   ->
Python Client
   ->
LLM
   ->
Tool Request
   ->
MCP Client Session
   ->
MCP Server
   ->
Rick and Morty API
   ->
MCP Server Result
   ->
LLM Final Answer
   ->
User
```

---

## Tool exposed by server

### `find_rick_and_morty_character`

Searches the Rick and Morty API by full or partial character name.

#### Input

```json
{
  "name": "Rick"
}
```

#### Output

Returns matching characters with fields like:

- `id`
- `name`
- `status`
- `species`
- `type`
- `gender`
- `origin`
- `location`
- `episode_count`
- `image`
- `url`

---

## Requirements

- Python 3.10+
- PowerShell (if using `run.ps1`)
- internet connection
- Hugging Face token if using Hugging Face router
- required Python packages:
  - `mcp`
  - `httpx`
  - `openai`

Install manually:

```bash
pip install mcp httpx openai
```

---

## How to run

### 1. Create virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

#### Windows PowerShell

```powershell
. .\.venv\Scripts\Activate.ps1
```

### 3. Install packages

```bash
pip install -U mcp httpx openai
```

### 4. Configure model and token

If your client uses hardcoded values, edit them in `client.py`:

```python
MODEL = "meta-llama/Llama-3.1-8B-Instruct:cerebras"
HF_TOKEN = "your_token_here"
```

If your model/provider does not support native tool calling correctly, the client may return tool-like JSON in text instead of real structured tool calls.

### 5. Run

```bash
python client.py
```

Or with a custom query:

```bash
python client.py "Who is Morty Smith?"
```

Or via PowerShell script:

```powershell
.\run.ps1 "Who is Rick Sanchez?"
```

---

## Example flow

### User asks

```text
Who is Rick Sanchez?
```

### Client sends

- system message
- user message
- tool definitions derived from MCP server

### LLM may respond with tool request

```json
{
  "name": "find_rick_and_morty_character",
  "arguments": {
    "name": "Rick Sanchez"
  }
}
```

### Client calls MCP tool

```python
await session.call_tool("find_rick_and_morty_character", {"name": "Rick Sanchez"})
```

### MCP server fetches data

The server queries:

```text
https://rickandmortyapi.com/api/character
```

and all paginated results.

### Final answer

The client sends the tool result back to the LLM and prints a natural-language answer.

---

## Important note about tool calling

This project can be implemented in two ways:

### 1. Prompt-based tool calling
The LLM is told in plain text to return JSON for tool usage.

Example:

```python
PROMPT = """
Use the tool when needed.
Return JSON in this format:
{"tool":"find_rick_and_morty_character","arguments":{"name":"Rick"}}
"""
```

This is simple, but unreliable.

### 2. Native tool calling
The client sends tools separately as schema:

```python
tools=[...]
tool_choice="auto"
```

This is the more standard production pattern.

However, not every model/provider combination supports native tool calling reliably. Some models may output JSON-like text in `message.content` instead of returning structured `tool_calls`.

---

## Known issue

You may see this behavior:

```text
Final answer:
{"name": "find_rick_and_morty_character", "arguments": {"name": "Rick"}}
```

This means the model returned a **tool-like text response** instead of a proper structured tool call.

### Why this happens

- model/provider may not fully support native tool calling
- tool-calling support may be inconsistent
- `tool_choice="auto"` may still produce plain text content

### Workarounds

- force tool usage
- add fallback JSON parsing from `message.content`
- use app-side routing
- switch to a model/runtime with stronger tool-calling support
- skip LLM decision and always call MCP for character queries

---

## Recommended learning path

If your goal is to understand MCP clearly:

### Version 1
Always call the MCP tool directly from the client.

### Version 2
Let the LLM summarize MCP tool results.

### Version 3
Let the LLM decide whether to call tools.

This helps separate:

- MCP mechanics
- LLM behavior
- provider-specific tool-calling issues

---

## Sample server behavior

Server exposes:

```python
@server.list_tools()
async def list_tools() -> list[types.Tool]:
```

and:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
```

That means:

- MCP clients can discover tools
- MCP clients can invoke tools
- server is the source of truth for available tools

---

## Why dynamic tool mapping is useful

Instead of hardcoding tool definitions in the client, a better design is:

1. client asks MCP server for tools
2. client converts them to LLM schema
3. LLM chooses tool
4. client forwards tool call to MCP server

Benefits:

- no duplication
- single source of truth
- easier to add more tools later

---

## Future improvements

Possible improvements:

- cache Rick and Morty API responses
- support exact match vs partial match
- return fewer or ranked matches
- add episode lookup tool
- add location lookup tool
- support Ollama or local model runtime
- add fallback parser when native tool calling fails
- add better logging and error handling

---

## Disclaimer

This project is for learning and experimentation.

It demonstrates:

- MCP server/client flow
- tool exposure
- tool invocation
- LLM integration patterns

It is not production-ready without:

- token security
- retries
- caching
- provider compatibility handling
- structured logging
- better validation

---

## Summary

This project helps you understand:

- what MCP server does
- what MCP client does
- how LLMs use tools
- difference between prompt-based and native tool calling
- why provider/model support matters
