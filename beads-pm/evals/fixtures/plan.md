# Plan: add a `sync` subcommand to sbxcli

sbxcli is a small CLI tool (src/sbxcli/) that currently supports `sbxcli push`
and `sbxcli pull` against a remote HTTP endpoint. We want to add a `sync`
subcommand that reconciles local and remote state, plus the supporting pieces
it needs.

## Background

The tool already has:
- `src/sbxcli/config.py` -- loads `~/.sbxcli/config.toml`, has a `Config` class
- `src/sbxcli/client.py` -- thin HTTP client wrapper (`Client.get`, `Client.put`)
- `src/sbxcli/commands/push.py` and `pull.py` -- existing subcommands
- `src/sbxcli/cli.py` -- argparse entrypoint that registers subcommands

## What sync needs to do

1. Add a local state cache at `~/.sbxcli/state.json` tracking the last-synced
   revision per remote path. Needs a small `StateStore` class with `load()`,
   `save()`, and `get_revision(path)` / `set_revision(path, rev)`.

2. Add a diff engine that, given local files under a configured sync root and
   the remote listing (via `Client.get("/list")`), computes which files are
   new locally, new remotely, changed on both sides (conflict), or unchanged.
   This is pure logic, no I/O, should live in its own module so it's easy to
   test with fixtures.

3. Add retry-with-backoff to `Client` for the sync subcommand's requests
   specifically -- push/pull should keep their current fire-once behavior.
   We haven't decided yet whether that's exponential backoff or a fixed
   schedule; need to weigh it against what the server's rate limiter expects
   before committing to one.

4. Wire up `sbxcli sync [--dry-run]` in `cli.py`: loads config, loads state,
   fetches remote listing, runs the diff engine, and for `--dry-run` just
   prints the plan; otherwise applies non-conflicting changes and reports
   conflicts to the user without resolving them.

5. Decide on the on-disk format for `state.json` (flat map of path->revision,
   vs. something with timestamps and checksums too) -- want to leave room for
   a future `sbxcli sync --status` command that shows staleness per file
   without over-building it now.

6. Update the README's command table to list `sync` alongside `push`/`pull`.

Once this lands we also want conflict resolution (`--prefer-local` /
`--prefer-remote` flags) but that's out of scope for this pass -- flag it as
a follow-on.
