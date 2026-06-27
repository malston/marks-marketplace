# MCP (Model Context Protocol) Reference

## Architecture Overview

```
Your Application Server
        ↕
   MCP Client          ← your code wraps this
        ↕
   MCP Server          ← tools + resources + prompts
        ↕
  External Service     ← GitHub API, Slack, AWS, etc.
```

**Why MCP over direct tool use**: MCP server maintainers (often service providers) write and maintain the tool schemas and implementations. You just connect a client.

## Server Implementation (Python SDK)

```bash
pip install mcp pydantic
```

```python
from mcp import FastMCP
from pydantic import Field
from mcp.types import UserMessage

mcp = FastMCP("my-server")

# In-memory store (replace with real data source)
docs = {
    "doc1": "Project proposal content...",
    "doc2": "Meeting notes..."
}

# --- TOOLS (reactive: Claude calls when needed) ---

@mcp.tool(
    name="read_document",
    description="Reads a document by its ID. Returns the full document text. "
                "Use when the user asks about a specific document."
)
def read_document(
    doc_id: str = Field(description="The document identifier (e.g. 'doc1')")
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found. Available: {list(docs.keys())}")
    return docs[doc_id]

@mcp.tool(
    name="edit_document",
    description="Replaces text in a document. Use for targeted edits."
)
def edit_document(
    doc_id: str = Field(description="Document to edit"),
    old_string: str = Field(description="Exact text to find and replace"),
    new_string: str = Field(description="Replacement text")
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found")
    if old_string not in docs[doc_id]:
        raise ValueError(f"String not found in document")
    docs[doc_id] = docs[doc_id].replace(old_string, new_string, 1)
    return f"Successfully updated {doc_id}"

# --- RESOURCES (proactive: clients fetch directly) ---

@mcp.resource("docs://documents", mime_type="application/json")
def list_documents() -> dict:
    """List all available documents."""
    return {"documents": list(docs.keys())}

@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def get_document(doc_id: str) -> str:
    """Get a specific document by ID."""
    return docs.get(doc_id, "")

# --- PROMPTS (pre-built templates for clients) ---

@mcp.prompt(
    name="format_document",
    description="Formats a document as clean markdown"
)
def format_document_prompt(doc_id: str) -> list:
    return [UserMessage(
        f"Please read the document with ID '{doc_id}' using the read_document tool, "
        f"then reformat its content as clean, well-structured markdown. "
        f"Save the reformatted version using edit_document."
    )]

if __name__ == "__main__":
    mcp.run()
```

**Test with MCP Inspector**:
```bash
mcp dev server.py
# Opens browser at localhost:PORT
# Connect → Tools → select tool → input params → Run
```

## Client Implementation

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

class MCPClient:
    def __init__(self):
        self.session = None

    async def connect(self, server_script: str):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script]
        )
        stdio_transport = await stdio_client(server_params).__aenter__()
        self.session = ClientSession(*stdio_transport)
        await self.session.__aenter__()
        await self.session.initialize()

    async def list_tools(self) -> list:
        result = await self.session.list_tools()
        return result.tools  # list of tool schema objects

    async def call_tool(self, name: str, input: dict) -> str:
        result = await self.session.call_tool(name, input)
        return result.content[0].text

    async def read_resource(self, uri: str):
        result = await self.session.read_resource(uri)
        resource = result.contents[0]
        if resource.mime_type == "application/json":
            return json.loads(resource.text)
        return resource.text

    async def list_prompts(self) -> list:
        result = await self.session.list_prompts()
        return result.prompts

    async def get_prompt(self, name: str, arguments: dict) -> list:
        result = await self.session.get_prompt(name, arguments)
        return result.messages  # ready to send directly to Claude

    async def close(self):
        await self.session.__aexit__(None, None, None)
```

## Integrating MCP Client with Claude

```python
async def chat_with_mcp(user_message: str, mcp_client: MCPClient) -> str:
    # Get tools from MCP server in Claude-compatible format
    mcp_tools = await mcp_client.list_tools()
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema
        }
        for t in mcp_tools
    ]

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=1024,
            tools=tools, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await mcp_client.call_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        messages.append({"role": "user", "content": tool_results})

    return " ".join(b.text for b in response.content if hasattr(b, "text"))
```

## Resources vs. Tools vs. Prompts

| Component | Triggered By | Use For |
|-----------|-------------|---------|
| **Tool** | Claude decides to call it | Actions, mutations, real-time data |
| **Resource** | Client fetches directly (e.g. @ mention) | Reading data proactively |
| **Prompt** | Client invokes by name + args | Pre-built expert prompt templates |

## Transport Options

- **stdio** (most common for local) — client and server communicate via stdin/stdout
- **HTTP/SSE** — for remote servers or web deployments
- **WebSockets** — bidirectional streaming use cases

## Common MCP Servers (Official)

- `@anthropic/mcp-server-github` — repos, PRs, issues
- `@aws/mcp` — AWS services
- `mcp-server-filesystem` — local file operations
- `mcp-server-sqlite` — SQLite database access

Find more at: https://github.com/modelcontextprotocol/servers
