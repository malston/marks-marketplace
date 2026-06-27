# Tool Use Reference

## Tool Function Best Practices

```python
def get_current_datetime(date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Well-named functions and args help Claude understand tool purpose."""
    if not date_format:
        raise ValueError("date_format cannot be empty")  # Errors visible to Claude
    return datetime.now().strftime(date_format)
```

Rules:
- Use descriptive function and argument names
- Validate inputs and raise errors with helpful messages
- Error messages are returned to Claude so it can retry with corrections

## Tool Schema Structure

```python
from anthropic.types import ToolParam

get_current_datetime_schema = ToolParam({
    "name": "get_current_datetime",
    "description": "Returns the current date and time in the specified format. "
                   "Use this when you need to know the exact current time. "
                   "Returns a formatted datetime string.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "strftime format string (e.g. '%Y-%m-%d %H:%M:%S')"
            }
        },
        "required": []
    }
})
```

**Schema generation trick**: Paste your Python function to Claude.ai and ask:
> "Write a valid JSON schema spec for tool calling for this function, following Anthropic API tool use documentation best practices."

## Complete Multi-Tool Loop

```python
import json

TOOLS = [get_current_datetime_schema, add_duration_schema, set_reminder_schema]

def run_tool(name: str, tool_input: dict):
    """Dispatcher — routes tool names to implementations."""
    if name == "get_current_datetime":
        return get_current_datetime(**tool_input)
    elif name == "add_duration_to_datetime":
        return add_duration_to_datetime(**tool_input)
    elif name == "set_reminder":
        return set_reminder(**tool_input)
    else:
        raise ValueError(f"Unknown tool: {name}")

def run_tools(message) -> list:
    """Process all tool_use blocks in a message."""
    tool_results = []
    for block in message.content:
        if block.type == "tool_use":
            try:
                result = run_tool(block.name, block.input)
                is_error = False
                content = json.dumps(result)
            except Exception as e:
                is_error = True
                content = str(e)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,   # must match original tool_use block ID
                "content": content,
                "is_error": is_error
            })
    return tool_results

def run_conversation(initial_messages: list) -> str:
    """Main agent loop — continues until Claude stops requesting tools."""
    messages = initial_messages[:]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        messages.append({"role": "user", "content": tool_results})

    # Extract text from potentially multi-block response
    return " ".join(
        block.text for block in response.content
        if hasattr(block, "text")
    )
```

## Structured Data Extraction via Forced Tool Call

```python
extract_schema = {
    "name": "extract_contact",
    "description": "Extract contact information from text",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"}
        },
        "required": ["name"]
    }
}

response = client.messages.create(
    model=MODEL, max_tokens=512,
    tools=[extract_schema],
    tool_choice={"type": "tool", "name": "extract_contact"},
    messages=[{"role": "user", "content": "John Smith, john@example.com, 555-1234"}]
)
structured = response.content[0].input  # already a dict, no parsing needed
```

Use `tool_choice` when reliability matters more than simplicity. Prompt-based extraction is fine for quick/simple cases.

## Built-in Tool Schemas

### Web Search
```python
web_search_tool = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,                              # total search cap
    "allowed_domains": ["nih.gov", "cdc.gov"]  # optional domain restriction
}
```

Response block types: `text`, `tool_use` (the search query), `web_search_result` (pages found), `citation` (sourced quotes).

### Text Editor Tool
```python
# Schema stub — Claude expands it internally
text_editor_tool = {
    "name": "str_replace_based_edit_tool",
    "type": "text_editor_20250124"  # version varies by model: 20241022 for 3.5
}
```

Operations Claude will request: `view`, `str_replace`, `create`, `undo_edit`.
You must implement the actual file system operations and return results.

### Code Execution
```python
code_exec_tool = {
    "name": "code_execution",
    "type": "code_execution_20250522"
}
# Claude runs Python in isolated Docker container (no network)
# Pair with Files API to pass data in/out
```

## Batch Tool

Enables parallel tool calls in a single assistant message turn.
Define a `batch` tool that accepts a list of tool calls:

```python
batch_schema = {
    "name": "batch",
    "description": "Run multiple tools in parallel. Use when multiple independent tool calls are needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "tool_input": {"type": "object"}
                    }
                }
            }
        }
    }
}

def run_batch(calls: list) -> list:
    """Execute batch tool calls (can be parallelized with asyncio)."""
    results = []
    for call in calls:
        result = run_tool(call["tool_name"], call["tool_input"])
        results.append(result)
    return results
```

## Fine-Grained Tool Streaming

By default, the API buffers and validates JSON before streaming tool arguments.
Enable fine-grained mode for immediate streaming (at the cost of client-side validation):

```python
# In your streaming setup
response = client.messages.create(
    ...,
    betas=["fine-grained-tool-streaming-2025-05-14"]
)
# Handle input_json_delta events alongside content_block_delta
# partial_json = latest chunk; snapshot = cumulative JSON string so far
# Must handle potential invalid JSON (e.g. "undefined" instead of null)
```

Trade-off: default = slower but valid JSON; fine-grained = faster but requires error handling.

## Files API

```python
# Upload once
with open("data.csv", "rb") as f:
    file_obj = client.beta.files.upload(file=f)
file_id = file_obj.id

# Reference by ID in requests (works with code execution)
{"type": "document", "source": {"type": "file", "file_id": file_id}}
```
