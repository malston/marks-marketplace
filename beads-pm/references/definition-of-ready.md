# Definition of ready

Seeded by `bd-pm-init`. This copy lives in the repo it describes, at
`.claude/definition-of-ready.md`, because half of it is project-specific: the
test command, the layout, what counts as a reasonable slice here. Edit it.

It sits under `.claude/` rather than `.beads/` because `.beads/` holds the Dolt
database that `bd` manages. Foreign files in there are at the mercy of whatever
`bd doctor` and the migrations decide to do with the directory.

Everything that reads a bead reads this file: the filer before it writes one,
the auditor when it judges one, the worker loop before it claims one. Change
the file and all three change together.

## A bead is ready when all seven hold

1. **The title names a change.** A verb and an object. `Add retry to the S3
   uploader` passes. `S3 uploader` does not, and neither does `Investigate
   flaky uploads`, which is a question wearing a task's clothes.

2. **There is one outcome.** If the description has an "and then" in it, that
   is two beads with an edge between them. The test: can a worker close this
   bead having done only part of it? If yes, split.

3. **The files are named.** Paths, or a package, or a directory. The worker
   starts with no memory of the plan that produced this bead, so anything it
   has to go hunting for is context it spends before writing a line.

4. **The test that proves it is described.** Name the test, or say what the
   test has to demonstrate. A bead whose proof is "it works now" gives a worker
   nothing to write first and nothing to mutate afterwards.

5. **Dependencies are edges, not sentences.** `after the config refactor` in a
   description is invisible to `bd ready`, so the scheduler will hand this bead
   out early and a worker will burn a session discovering the blocker. Put it
   in the graph.

6. **No open design question.** If the bead asks whether to keep something,
   which of two approaches to take, or what the behaviour should be, it is a
   decision and it belongs to a person. Tag it `human` and leave it out of the
   work set.

7. **It fits one session.** A worker gets one context window for a failing
   test, a fix, a mutation round, a pull request and a review pass. Beads that
   touch more than a handful of files rarely survive that.

## Acceptance criteria, written for an agent

The reader has not seen the epic. Write so the bead stands alone.

```
Done when:
- `parse_duration("")` raises ConfigError instead of returning None
- tests/test_config.py::test_empty_duration covers it
- `make test` is green
```

Avoid the user-story form. "As a user I want" spends tokens on a persona the
worker cannot act on.

## Project specifics

<!-- Fill these in. The auditor reads them verbatim. -->

- Test command: `make test`
- Source layout:
- Reasonable slice size:
- Things that always need a `human` tag here:
