# Definition of ready

Seeded by `bd-pm-init`. This copy lives in the repo it describes, at
`.claude/definition-of-ready.md`, because half of it is project-specific: the
test command, the layout, what counts as a reasonable slice here. Edit it.

## A bead is ready when all seven hold

1. **The title names a change.** A verb and an object.
2. **There is one outcome.** If the description has an "and then" in it, split it.
3. **The files are named.** Paths, or a package, or a directory.
4. **The test that proves it is described.**
5. **Dependencies are edges, not sentences.**
6. **No open design question.** Tag it `human` instead.
7. **It fits one session.**

## Acceptance criteria, written for an agent

```
Done when:
- `parse_duration("")` raises ConfigError instead of returning None
- tests/test_config.py::test_empty_duration covers it
- `make test` is green
```

## Project specifics

- Test command: `pytest`
- Source layout: `src/sbxcli/` for code, `tests/` for tests, one module per subcommand
- Reasonable slice size: one subcommand or one shared module per bead
- Things that always need a `human` tag here: choice of config file format, choice of retry/backoff policy
