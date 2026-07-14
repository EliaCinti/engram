# Contributing to wadachi 轍

Thanks for stopping by. Wadachi is a small, handcrafted project — contributions
are welcome, and so is simply telling us how you use it.

## Philosophy (read this first)

1. **Local-first, privacy-first.** No telemetry, no cloud calls, no exceptions.
   Anything that would send user data anywhere gets rejected.
2. **Memories are sacred.** No change may lose or silently rewrite user
   memories. Schema changes go through migrations (with automatic backup);
   file-format changes go through the tolerant parser + backfill.
3. **Propose, never auto-edit.** Wadachi suggests (stale beliefs, insights,
   consolidation candidates) — the human or their agent decides.
4. **Degrade gracefully.** Every feature must work (or fail with a helpful
   message) without optional dependencies like `fastembed`.

## Dev setup

```bash
git clone https://github.com/EliaCinti/wadachi.git
cd wadachi
python -m venv venv && source venv/bin/activate
pip install -e ".[semantic,dev]"
pytest tests/ -q          # everything must be green before and after your change
```

Tests are hermetic (temporary `BRAIN_DIR`s) and must stay that way: never touch
a real brain in tests. The suite also runs without `fastembed` (CI does exactly
that) — semantic-only tests must skip cleanly.

## Making changes

- **Schema changes** → add a `wadachi/migrations/000N_*.py` script (see the
  contract in `migrations/__init__.py`: one `conn.execute` per statement,
  **never** `executescript`). Update the version-agnostic tests if needed.
- **New tools** → use the `@tool()` decorator (instrumented logging), return
  JSON strings, handle missing ids/malformed input without raising, add tests
  in `tests/test_tools.py`.
- **Logging** → never write to stdout (it is the MCP stdio channel). Use the
  `wadachi` logger.
- **Style** → match the surrounding code. Italian comments are fine (the
  maintainer is Italian); public docstrings in English.

## Submitting

1. Fork, branch (`feat/...`, `fix/...`), commit with a clear message.
2. `pytest tests/ -q` green.
3. Open a PR describing *what* and *why*. Small PRs get reviewed fast.

## Not a coder?

The most valuable contribution is feedback: open a
["Share your setup"](https://github.com/EliaCinti/wadachi/issues/new?template=share_your_setup.yml)
issue and tell us how you use wadachi. There is no telemetry — this is the
only way we learn what works.
