---
name: "be-ambitious"
description: "Raise the ambition of a task or prompt using Altitude, Depth and Range, write the plan and a rewritten prompt, then do the work when given a task. Use for /be-ambitious, \"aim higher\", \"raise the bar\", \"go deeper\"."
---

# Be Ambitious

Based on Felix Rieseberg's post "How to be more ambitious: A tutorial for humans with models" (felixrieseberg.com, October 2026). He names four types of ambition. Speed (same work, less time) is the default and this skill skips it. The other three are the point:

- **Altitude**: aim at the outcome the task serves. Ask what should happen next, and what the goal beyond the goal is.
- **Depth**: do the task the way the best person in the field would. Start from raw data, use their real methods and tools, and have something outside the model check the result.
- **Range**: pull in other fields and do what their experts actually do.

## Triggers

Use when the user types `/be-ambitious`, or says "be more ambitious", "aim higher", "go deeper on this", "what's the goal beyond the goal", "what would a top expert do here", "raise the bar", or asks to make a prompt more ambitious.

## Step 1: Figure out what you were handed

Decide which mode applies:

- **Prompt mode**: the user gave a prompt and wants it improved. Output the plan and the rewritten prompt. Stop there.
- **Task mode**: the user gave work to do (or invoked the skill on the current task in the conversation). Output the plan and the rewritten prompt, then do the work.

If the input is a bare `/be-ambitious` with nothing after it, apply it to the most recent task in the conversation. If there is no task, ask for one in a single sentence.

Restate the original ask in one line so the user can see what you are raising.

## Step 2: Altitude

Climb up from the task to the outcome.

1. Ask "why does this task exist?" and answer it. Then ask it again of that answer. Two or three climbs is usually enough.
2. Name the outcome the user actually wants. Example: "fix this crash" climbs to "keep the app crash-free".
3. Find the decisions the work feeds. If people will meet to discuss the output, the outcome is probably a decision. Name the top decisions and plan to give options with for and against arguments.
4. Ask whether the artifact itself is the best way to reach the outcome. A weekly status report exists so leaders catch problems early. A better design might be an alert that fires when a metric drifts. If you propose a replacement, plan to show from the user's own history that it would have worked better, and suggest running it beside the current approach for one cycle.
5. Name what the model needs in place to work at that level without a human feeding it tasks: data access, a way to map versions to commits, machines to reproduce bugs on, credentials, connectors. List anything missing.

When to hold back: altitude fits work with a real end goal. It fits creative work poorly. If the task is a poem, a design exploration, or something the user wants done exactly as stated, keep altitude light and say so.

## Step 3: Depth

Push the task down to the level a field-leading expert works at. Answer these four questions in writing:

1. **What would a top professional do here that the user did not ask for?**
2. **What raw material would they start from?** Logs, source data, primary documents, the actual codebase, the database. Prefer it over summaries, dashboards or someone's slide.
3. **Which methods and tools would they use?** Name them. A statistician uses a database and a model, not a markdown table. A performance engineer uses a profiler and flame graphs, not guesses. Switching vocabulary without switching methods does not count.
4. **What outside judge would show the result is right?** Something other than the model or the user: a test suite, a benchmark, a holdout dataset, a compiler, a linter, a real reproduction, a load test, a citation that checks out, or a separate reviewer agent that never saw the work being produced. Prefer a judge the model can run itself for fast feedback.

Then apply these moves where they fit:

- **Set an unreasonable target and treat it as reasonable.** Asked for 5 seconds? Aim for 200 milliseconds. If the work looks impossible partway through, keep going before calling it.
- **Challenge what the user believes.** Pick the key assumption behind the task and try to reproduce it from raw data. "We think churn is an onboarding problem" becomes a test.
- **Produce new knowledge.** Once deep in the data, look for a signal or blind spot nobody has found yet, and show it holds on data it was not built from.

## Step 4: Range

Bring in fields beyond the obvious one.

1. **Swap nouns for verbs.** Describe the deliverable as what it does. "A deck" becomes "getting busy people to trust a cause-and-effect story and decide under uncertainty in 30 minutes." The verbs point to fields.
2. **Assemble the crew.** Imagine the stakes are huge. Which experts would you hire? Include at least one adversary: a red team, a short seller, a forensic accountant, a security auditor, a skeptical reviewer.
3. **For each field, write down what that expert does**, as concrete actions and tools. Example: a journalist interviews the source data for the one story it supports. A short seller hunts for the number that does not reconcile. An editor cuts everything that does not move the reader.

Watch for role play. Asking the model to sound like a short seller changes tone and nothing else. Ask it to do the research a short seller does. If a field adds only flavor, drop it.

## Step 5: Choose the dial

You do not have to max out all three. Pick the dimension that changes the result most for this task and lead with it. Say in one line why the others are lighter. A good plan usually has one dimension doing most of the work and the other two adding a step each.

Check scope before raising it. If the ambitious version is expensive, slow, hard to reverse, touches production, or needs access you lack, say so in the plan. In task mode, ask before starting any part that is irreversible or a big jump in cost. Otherwise proceed.

## Step 6: Write the output

Use this structure. Keep it tight. Each section should be a few lines, not an essay.

```markdown
## Original ask
<one line>

## Altitude
Goal beyond the goal: <outcome>
Decisions this feeds: <list>
What needs to be in place: <access, data, tools; flag gaps>

## Depth
What a top expert would add: <...>
Raw material: <...>
Methods and tools: <...>
Outside judge: <...>
Target: <the unreasonable but stated-as-reasonable bar>
Assumption to challenge: <...>

## Range
As verbs: <...>
Crew and what each does: <field: action, tool>

## Plan
<numbered steps, ordered, each one checkable>

## Rewritten prompt
<a complete, standalone prompt that asks for exactly the plan above>
```

Rules for the rewritten prompt:

- It must stand on its own. Someone pasting it into a fresh session should get the ambitious version without reading the plan.
- State the outcome, the raw sources, the methods, the target, and the outside judge explicitly.
- Name the adversarial check.
- Ask for decisions with tradeoffs when the work feeds a decision.
- Keep it in plain language. No persona lines like "You are a world-class...". Describe the work instead.

## Step 7: Do the work (task mode only)

1. Set up the outside judge first, before producing the result, so you have something to check against. Write the test, pull the holdout set, define the benchmark.
2. Gather the raw material. If you cannot reach a source, say which one and continue with what you have.
3. Execute the plan with the real tools the experts would use. Install what you need.
4. Run the judge. Report the actual result against the target, including misses.
5. For high-stakes work, have a separate agent that did not see the work review it.
6. Finish with: what came out, how the judge scored it, the gaps that remain, and the one next step that would raise it further.

Do not grade your own work and call it verified. If no outside judge was possible, say so plainly.

## Failure modes to avoid

- Making the task bigger without making it better. More slides or more words is not ambition. Depth beats size.
- Vocabulary without method. Expert words with amateur tools.
- Role play in place of action in Range.
- Self-grading presented as verification.
- Forcing altitude onto creative or exact-spec work.
- Raising scope on something irreversible without asking.

## Short example

Original ask: "Write a Go benchmark for our JSON (JavaScript Object Notation) parser."

- Altitude: the goal is keeping request latency low as payloads grow. Plan a continuous benchmark in CI (continuous integration) that fails the build on regression.
- Depth: start from real production payload samples, not synthetic ones. Use `go test -bench` with `benchstat` across runs, `pprof` CPU and allocation profiles. Target a 5x allocation cut. Judge: benchstat significance on 10+ runs and the existing test suite still passing.
- Range: a database engineer would check whether a streaming decoder or code-generated decoder removes reflection. An SRE (site reliability engineer) would tie the benchmark to the p99 latency SLO (service level objective).
- Rewritten prompt then asks for all of that in one standalone request.