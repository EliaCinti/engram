# CLI reference

Everything accepts `--brain-dir PATH` (or the `BRAIN_DIR` env var; fallback
`~/.wadachi`, legacy `~/.engram` honored).

## wadachi

No arguments → runs the MCP server on stdio. This is what your client launches;
you rarely run it by hand.

## wadachi init

Guided setup: brain dir, migrated DB, `SCHEMA.md`, `index.md`, Claude Code and
Antigravity registration. Idempotent. Flags: `--brain-dir`, `--no-claude`,
`--no-antigravity`. Details in [[installation]].

## wadachi doctor

Read-only diagnosis: dir & permissions, DB integrity, schema version vs available
migrations, missing/orphan/malformed files, wiki files, search mode, MCP
registration. Exit code 0/1.

`--fix` repairs **only what's safe**: missing directories, non-canonical frontmatter
(regenerated from the DB, prose untouched), regenerated index, missing SCHEMA.md.
`--no-mcp` skips the client check. See [[troubleshooting]].

## wadachi sleep

The consolidation report ([[sleep]]) — read-only, caches results so the next
`get_context` proposes them. Built for cron.

## wadachi obsidian

On-demand wikilink backfill for the Obsidian graph ([[obsidian-okf]]).
`--dry-run` previews. Never runs automatically.

## wadachi export

Portable snapshot of the whole brain — strictly read-only, safe even before an
upgrade or on a legacy Engram brain. `--out FILE` to choose the destination.
See [[safety]].

## wadachi restore

`--to <new-dir>` restores an export somewhere fresh (refuses non-empty targets
without `--force`). `--replace` swaps the **active** brain, safety-exporting the
current state first. See [[safety]].

## Environment

| var | effect |
|---|---|
| BRAIN_DIR | where the brain lives |
| WADACHI_LOG | log level for `logs/wadachi.log` (default INFO; DEBUG adds per-tool timings) |
