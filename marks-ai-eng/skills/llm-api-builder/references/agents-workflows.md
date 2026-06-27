# Agents & Workflows Reference

## Decision Framework

**Use workflows when**: You know the exact steps in advance, reliability is critical, the task is predictable.

**Use agents when**: Steps are unknown, flexibility is required, the same toolset needs to handle varied tasks.

**Default to workflows** — users want 100% working products over clever agents.

| Dimension | Workflows | Agents |
|-----------|-----------|--------|
| Steps | Predetermined | Dynamic |
| Testing | Easy (known path) | Hard (unpredictable) |
| Success rate | Higher | Lower |
| User input | Specific, structured | Natural language |
| Flexibility | Low | High |

---

## Workflow Patterns

### Pattern 1: Chaining

Sequential steps where each output feeds the next. Use when:
- Single prompts consistently violate multiple constraints
- Tasks have natural sequential phases
- You need to separate generation from refinement

```python
def chaining_workflow(topic: str) -> str:
    # Step 1: Generate initial content
    draft = chat([{"role": "user", "content": f"Write a blog post about {topic}"}])

    # Step 2: Enforce constraints as separate pass
    final = chat([{
        "role": "user",
        "content": f"""Rewrite the following blog post with these constraints:
        - No mention of AI or artificial intelligence
        - No emojis
        - Professional tone
        - Under 500 words

        <draft>{draft}</draft>"""
    }])
    return final
```

**Key insight**: Even simple-seeming tasks may need chaining when constraint lists grow long. Claude can't reliably satisfy 5+ simultaneous constraints in one pass.

### Pattern 2: Parallelization

Multiple Claude calls in parallel for independent subtasks, then aggregate. Use for:
- Multi-factor analysis
- Evaluating multiple options simultaneously
- Any task where subtasks don't depend on each other

```python
import asyncio
from anthropic import AsyncAnthropic

async_client = AsyncAnthropic()

async def analyze_material(material: str, criteria: dict) -> dict:
    response = await async_client.messages.create(
        model=MODEL, max_tokens=512,
        messages=[{"role": "user", "content":
            f"Evaluate {material} for: {criteria}. Return score 1-10 with reasoning."}]
    )
    return {"material": material, "analysis": response.content[0].text}

async def parallelization_workflow(materials: list, criteria: dict) -> str:
    # Run all material analyses in parallel
    tasks = [analyze_material(m, criteria) for m in materials]
    results = await asyncio.gather(*tasks)

    # Aggregate in a final call
    summary = chat([{"role": "user", "content":
        f"Compare these material analyses and recommend the best option:\n{results}"}])
    return summary
```

Structure: Input → N parallel subtasks → Aggregator → Output

### Pattern 3: Routing

First call categorizes input; system routes to specialized pipeline per category.

```python
CATEGORIES = ["educational", "entertainment", "news", "technical"]

PROMPTS = {
    "educational": "Write in a clear, instructive tone with definitions. Use examples.",
    "entertainment": "Use engaging hooks, casual language, and trending references.",
    "technical": "Be precise and detailed. Include code examples where relevant.",
    "news": "Lead with the key fact. Use journalistic style. Be objective."
}

def routing_workflow(topic: str) -> str:
    # Step 1: Categorize
    category_response = chat([{"role": "user", "content":
        f"Categorize this topic: '{topic}'\n"
        f"Categories: {CATEGORIES}\n"
        f"Respond with only the category name."}])
    category = category_response.strip().lower()

    # Step 2: Route to specialized pipeline
    style_guide = PROMPTS.get(category, PROMPTS["educational"])
    return chat([{"role": "user", "content":
        f"{style_guide}\n\nNow write content about: {topic}"}])
```

### Pattern 4: Evaluator-Optimizer

Producer generates output; evaluator scores it; loop continues until threshold met.

```python
def evaluator_optimizer_workflow(
    task: str,
    target_score: float = 8.0,
    max_iterations: int = 5
) -> str:
    current_output = ""
    feedback = ""

    for i in range(max_iterations):
        # Producer
        prompt = task if i == 0 else f"{task}\n\nPrevious attempt:\n{current_output}\n\nFeedback:\n{feedback}\n\nPlease improve:"
        current_output = chat([{"role": "user", "content": prompt}])

        # Evaluator
        eval_response = chat([{"role": "user", "content":
            f"Score this output 1-10 and explain what's wrong:\n{current_output}\n"
            f"Return JSON: {{score: N, issues: [...]}}"}])
        eval_data = json.loads(eval_response)

        if eval_data["score"] >= target_score:
            break

        feedback = "\n".join(eval_data["issues"])

    return current_output
```

---

## Agent Design

### Tool Design Principle: Abstract Over Specific

```
# Bad — hyper-specialized tools
refactor_code(file, pattern)
install_dependencies(package_list)
run_linter(config)

# Good — abstract tools Claude can combine flexibly
bash(command)
read_file(path)
write_file(path, content)
web_fetch(url)
```

Abstract tools enable Claude to combine them in unexpected ways. This is how Claude Code works.

### Environment Inspection

After every action, agents must inspect state — they cannot assume success.

```python
def agent_workflow(task: str, tools: list) -> str:
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=2048,
            tools=tools, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)

                # Environment inspection: include state verification
                if block.name == "bash":
                    # Claude gets stdout + stderr + exit code
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "exit_code": result.returncode
                        })
                    })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

        messages.append({"role": "user", "content": tool_results})

    return " ".join(b.text for b in response.content if hasattr(b, "text"))
```

**Computer use pattern**: Claude takes a screenshot after EVERY action (click, type, scroll) to see what changed, since it can't predict UI state from first principles.

### When Agents Request More Information

Design your agent loop to handle clarification requests:
```python
# Claude may produce a text response (not tool_use) asking for info
# When stop_reason != "tool_use", check if Claude is asking a question
# vs. providing a final answer — handle accordingly
```

---

## Production Recommendations

1. **Start with workflows** — convert to agent only when flexibility is genuinely required
2. **Test coverage** — workflows have deterministic paths; write integration tests for each step
3. **Timeouts** — set per-step timeouts in agent loops (Claude may chain many tools)
4. **Error recovery** — surface tool errors to Claude with full context; let it decide how to recover
5. **Observability** — log every tool call input/output for debugging
6. **Cost control** — use Haiku for routing/classification steps; Sonnet/Opus for complex reasoning
