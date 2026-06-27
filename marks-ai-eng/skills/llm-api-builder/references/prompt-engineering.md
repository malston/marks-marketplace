# Prompt Engineering Reference

## Technique Stack (apply in order)

### 1. Be Clear and Direct
Use an action verb in the first line. Highest single-impact change.

```
# Bad
"Can you maybe help me think about meal planning for athletes?"

# Good
"Generate a one-day meal plan for an athlete that meets their dietary restrictions."
```

Score impact example: 2.32 → 3.92

### 2. Be Specific (Attributes and Steps)

**Type A — Output Attributes** (almost always useful):
- Length targets ("3–5 sentences per section")
- Format requirements ("respond only in JSON")
- Structural constraints ("include exactly 3 recommendations")

**Type B — Reasoning Steps** (use for complex problems):
- Provide explicit steps for the model to follow
- Useful when Claude naturally omits important considerations

Score impact example: 3.92 → 7.86

### 3. Use XML Tags for Structure

```python
prompt = f"""
Generate a meal plan for the following athlete.

<athlete_information>
Height: {height}, Weight: {weight}, Goal: {goal}
Restrictions: {restrictions}
</athlete_information>
"""
```

Use specific tag names (`<sales_records>` > `<data>`). Works even for short content.

### 4. Provide Examples (One-shot / Multi-shot)

```python
prompt = """
Generate a meal plan for the athlete below.

<example>
<input>Height: 5'10", Weight: 180 lbs, Goal: muscle gain, Restrictions: vegetarian</input>
<ideal_output>
Breakfast (7am): Greek yogurt parfait | 420 cal | 35g protein | 45g carbs
</ideal_output>
<why_ideal>Includes protein target, respects vegetarian constraint, specifies macros.</why_ideal>
</example>

<athlete_information>{athlete_info}</athlete_information>
"""
```

Best practices:
- Add context for edge cases before examples ("be especially careful with sarcasm")
- Include reasoning for why each example is ideal
- Use your highest-scoring eval outputs as templates
- Place examples after main instructions

### 5. System Prompts

Control HOW Claude responds:
```python
system = "You are a certified sports nutritionist. Give evidence-based recommendations.
         When requirements are ambiguous, ask clarifying questions."
```

---

## Eval Workflow

### Full 6-Step Process

1. Write initial prompt (don't pre-optimize)
2. Generate test dataset (use Haiku for speed)
3. Interpolate each case into prompt template
4. Run LLM on each, collect outputs
5. Grade each output, average scores
6. Iterate — compare score deltas between versions

### Generating Datasets with Haiku

```python
def generate_dataset(n=20):
    messages = [
        {"role": "user", "content": f"Generate {n} athlete profiles as JSON array."},
        {"role": "assistant", "content": "```json"}
    ]
    response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=2000,
        messages=messages, stop_sequences=["```"]
    )
    return json.loads(response.content[0].text)
```

### Grader Implementations

**Code grader** — syntax validation, length checks, word presence:
```python
def code_grade(output):
    score = 0
    try:
        ast.parse(output); score += 5
    except SyntaxError:
        pass
    if len(output.split('\n')) < 100: score += 5
    return score  # 0-10
```

**Model grader** — ask for strengths/weaknesses/reasoning BEFORE score to prevent middle-clustering:
```python
GRADER_PROMPT = """Evaluate this response 1-10.
<request>{request}</request>
<response>{response}</response>
Return JSON: {strengths, weaknesses, reasoning, score}"""

def model_grade(request, response):
    messages = [
        {"role": "user", "content": GRADER_PROMPT.format(...)},
        {"role": "assistant", "content": "```json"}
    ]
    result = client.messages.create(..., stop_sequences=["```"])
    return json.loads(result.content[0].text)["score"]
```

**Combined**: `final = (model_score + syntax_score) / 2`

### Concurrency
```python
import asyncio
from anthropic import AsyncAnthropic

async def run_eval_async(dataset, max_concurrent=5):
    sem = asyncio.Semaphore(max_concurrent)
    # ... run all cases with semaphore
```

Adjust `max_concurrent` based on your rate tier.
