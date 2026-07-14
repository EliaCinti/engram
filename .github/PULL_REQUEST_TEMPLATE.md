## What & why

<!-- One or two sentences: what does this change, and what problem does it solve? -->

## Checklist

- [ ] `pytest tests/ -q` green (suite also passes without `fastembed`)
- [ ] No user memories can be lost or silently rewritten by this change
- [ ] Schema changes (if any) go through a `wadachi/migrations/000N_*.py` script
- [ ] No logging to stdout (MCP stdio channel), no telemetry, no cloud calls
- [ ] CHANGELOG.md updated if user-visible
