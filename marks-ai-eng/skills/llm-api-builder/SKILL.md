---
name: llm-api-builder
description: >
  Comprehensive reference for building with the Claude API — covering model selection,
  request structure, multi-turn conversations, tool use, RAG pipelines, streaming,
  prompt engineering, evals, MCP, agents, and workflows. Use this skill whenever the
  user asks about Claude API integration, SDK usage, tool calling, prompt caching,
  extended thinking, embeddings, retrieval, MCP servers/clients, agentic workflows,
  or any pattern for building production Claude-powered applications. Trigger even for
  partial mentions like "how do I call Claude from Python", "set up tool use", "build
  an agent", "implement RAG", "prompt caching", "MCP server", or "streaming responses".
---

# Building with the Claude API

Reference guide distilled from the Anthropic "Building with the Claude API" course.
For deep dives, see the reference files in `references/`.

---

## 1. Model Selection

| Model  | Best For | Trade-off |
|--------|----------|-----------|
| **Opus** | Complex multi-step reasoning, planning | Higher cost + latency |
| **Sonnet** | Balanced — coding, editing, most production tasks | Best default choice |
| **Haiku** | Real-time UX, high-volume processing | No extended reasoning |

**Rule**: Mix models in the same app — e.g. Haiku for dataset generation, Sonnet for production responses, Opus only where deep reasoning matters.

---

## 2. Core Request Structure

```python
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = "claude-sonnet-4-5"

response = client.messages.create(
    model=MODEL,
    max_tokens=1024,          # safety ceiling, not target length
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "What is quantum computing?"}
    ]
)
text = response.content[0].text
```

**Key parameters**
- `model` — model string (required)
- `max_tokens` — hard ceiling on output length (required)
- `messages` — list of `{role, content}` dicts (required)
- `system` — system prompt string (optional kwarg)
- `temperature` — 0–1; 0 = deterministic, ~1 = creative
- `stop_sequences` — list of strings that halt generation when hit

---

## 3. Multi-Turn Conversations

The API is **stateless** — no memory between requests. Maintain history manually.

```python
messages = []

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})

def chat(messages, system=None):
    params = {"model": MODEL, "max_tokens": 1024, "messages": messages}
    if system:
        params["system"] = system
    return client.messages.create(**params)

add_user_message(messages, "Hello!")
response = chat(messages)
add_assistant_message(messages, response.content[0].text)
```

---

## 4. Streaming

```python
with client.messages.stream(
    model=MODEL, max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="", flush=True)
    final = stream.get_final_message()  # for DB storage
```

Raw event types: `message_start` → `content_block_start` → `content_block_delta` (text) → `content_block_stop` → `message_stop`.

---

## 5. Controlling Output

### Pre-filling
Append an assistant message to steer continuation direction:
```python
messages = [
    {"role": "user", "content": "Compare coffee vs tea."},
    {"role": "assistant", "content": "Coffee is better because"}
]
```

### Stop sequences
```python
response = client.messages.create(
    ..., stop_sequences=["\n\n"]
)
```

### Clean structured output (pre-fill + stop)
```python
messages = [
    {"role": "user", "content": "Return a JSON list of 3 colors."},
    {"role": "assistant", "content": "```json"}
]
response = client.messages.create(..., messages=messages, stop_sequences=["```"])
```

---

## 6. Prompt Engineering

**Ordered by impact:**
1. **Clear + direct** — action verb first: `"Write..."`, `"Identify..."`, `"Generate..."`
2. **Specific** — add output attributes (length, format) or explicit reasoning steps
3. **XML tags** — wrap injected content: `<my_code>...</my_code>`, `<athlete_info>...</athlete_info>`
4. **Examples** — one-shot/multi-shot with XML wrappers + reasoning about why each is ideal
5. **System prompts** — shape HOW Claude responds (role, tone, constraints)

**Eval workflow before shipping any prompt:**
1. Write initial prompt
2. Generate test dataset (use Haiku for speed)
3. Run: `run_prompt()` per test case → grade → average scores
4. Iterate — compare score deltas across versions

**Grader types**: code graders (syntax/length checks), model graders (LLM 1–10 scores with reasoning), human graders (most flexible, slowest).

---

## 7. Extended Thinking

For hard tasks where prompt optimization isn't enough:

```python
response = client.messages.create(
    model=MODEL,
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 2048},
    messages=[...]
)
# response.content = [ThinkingBlock(...), TextBlock(...)]
```

- Thinking tokens are **billed** — enable only after evals confirm necessity
- Thinking blocks include a cryptographic signature (tamper-proof)
- Redacted thinking blocks may appear for safety-flagged content

---

## 8. Tool Use

See `references/tool-use.md` for full details.

### Core tool loop
```python
def run_conversation(messages, tools):
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
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": False
                })
        messages.append({"role": "user", "content": tool_results})
    return response
```

### Tool schema structure
```python
{
    "name": "get_current_datetime",
    "description": "Returns current date/time. Use when exact time is needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_format": {"type": "string", "description": "strftime format"}
        },
        "required": []
    }
}
```
**Tip**: Paste your Python function into Claude and ask it to generate the schema using Anthropic tool use docs.

### Built-in tool schemas (you implement execution)
- **Text editor**: `str_replace_based_edit_tool` (version-dated per model)
- **Web search**: `{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}`
- **Code execution**: server-side Docker container (no network); pairs with Files API

### Force a specific tool
```python
response = client.messages.create(
    ...,
    tool_choice={"type": "tool", "name": "extract_data"},
)
structured_output = response.content[0].input  # already a dict
```

---

## 9. Prompt Caching

Avoids reprocessing identical input. Cache lasts **1 hour**, minimum **1024 tokens**.

```python
# Cache system prompt
system = [{"type": "text", "text": long_prompt, "cache_control": {"type": "ephemeral"}}]

# Cache tool schemas (add to last tool)
tools_cached = tools[:]
tools_cached[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}

response = client.messages.create(model=MODEL, max_tokens=1024,
    system=system, tools=tools_cached, messages=messages)

# Verify hit: response.usage.cache_read_input_tokens > 0
```

**Rules**: Max 4 breakpoints per request. Processing order: tools → system → messages. Any change before a breakpoint invalidates that cache layer.

---

## 10. Multimodal (Images & PDFs)

```python
# Image
{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
    {"type": "text", "text": "Describe step by step."}
]}

# PDF
{"role": "user", "content": [
    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
    {"type": "text", "text": "Summarize the key findings."}
]}
```

- Max **100 images** per request; billed by pixel dimensions
- **Accuracy depends on prompt quality** — use step-by-step instructions and examples
- Enable citations: `"citations": {"enabled": True}` → response includes `citation_page_location` or `citation_char_location` blocks

---

## 11. RAG

See `references/rag.md` for full implementation.

**Pipeline**:
1. **Chunk** docs (size-based with overlap, structure-based on headers, or semantic)
2. **Embed** → numerical vectors (Voyage AI recommended by Anthropic)
3. **Store** in vector DB
4. **Query** → embed question → cosine similarity → retrieve top-k chunks
5. **Assemble** prompt with chunks + question → Claude

**Hybrid search** (better recall): vector + BM25 in parallel → merge with Reciprocal Rank Fusion: `RRF = Σ 1/(rank+1)` per doc.

**Reranking**: send candidates to Claude for semantic re-ordering after hybrid retrieval.

**Contextual retrieval**: prepend LLM-generated context to each chunk before indexing.

---

## 12. MCP (Model Context Protocol)

See `references/mcp.md` for full server/client implementation.

**Why MCP**: Eliminates writing tool schemas/implementations for third-party services. Service providers publish official MCP servers.

**Server (Python SDK)**:
```python
from mcp import FastMCP
mcp = FastMCP("my-server")

@mcp.tool(name="read_doc", description="Reads document by ID")
def read_doc(doc_id: str) -> str:
    return docs[doc_id]

@mcp.resource("docs://documents/{doc_id}", mime_type="application/json")
def get_doc(doc_id: str) -> dict:
    return docs.get(doc_id, {})

@mcp.prompt(name="format_doc")
def format_doc_prompt(doc_id: str) -> list:
    return [UserMessage(f"Read doc {doc_id} and reformat as markdown.")]
```

**Debug**: `mcp dev server.py` → MCP Inspector in browser.

**Client API**:
```python
tools    = await client.list_tools()
result   = await client.call_tool(name, input)
data     = await client.read_resource(uri)
messages = await client.get_prompt(name, args)
```

**Resources vs Tools**: Resources expose data proactively; tools execute actions when Claude decides to call them.

---

## 13. Agents & Workflows

See `references/agents-workflows.md` for patterns and decision framework.

| Use | When |
|-----|------|
| **Workflow** | Steps known in advance; reliability critical |
| **Agent** | Steps unknown; flexibility required |

**Prefer workflows** — users want 100% reliability.

**Workflow patterns**:
- **Chaining** — sequential steps; use when single prompts violate multiple constraints
- **Parallelization** — parallel subtasks → aggregate; use for multi-factor analysis
- **Routing** — first call categorizes → routes to specialized pipeline
- **Evaluator-optimizer** — producer → evaluator → loop until threshold met

**Agent principles**:
- Provide abstract tools (bash, file_read) over specialized ones (refactor_code)
- Implement **environment inspection** — read state after each action
- Loop on `stop_reason == "tool_use"`; break on any other stop reason

---

## Quick Reference

| Goal | Pattern |
|------|---------|
| Raw JSON output | Pre-fill ` ```json ` + stop sequence ` ``` ` |
| Force tool | `tool_choice={"type":"tool","name":"..."}` |
| Reduce cost | Prompt caching with `cache_control` |
| Large docs | RAG or Files API + code execution |
| Third-party services | MCP servers |
| Complex reasoning | Extended thinking |
| Better UX on long responses | `client.messages.stream()` |
| Constraint-heavy prompts | Chaining workflow (generate → fix violations) |

---

## Reference Files

- `references/prompt-engineering.md` — Techniques, eval workflow, grader implementations
- `references/tool-use.md` — Schemas, multi-tool loops, batch tool, fine-grained streaming
- `references/rag.md` — Chunking, embeddings, hybrid search, reranking, contextual retrieval
- `references/mcp.md` — Server/client implementation, resources, prompts, Inspector
- `references/agents-workflows.md` — Workflow patterns, agent design, environment inspection
