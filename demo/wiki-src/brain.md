# The brain on disk

Everything wadachi knows lives in **one directory you own**. No hidden state, no
cloud copy. This page is the map.

```
~/.wadachi/
├── SCHEMA.md      # the wiki conventions — yours to edit
├── index.md       # generated catalog: one line per memory
├── log.md         # append-only history of operations
├── brain.db       # SQLite: metadata, embeddings, beliefs, versions
├── backups/       # automatic backups (migrations, sessions, pre-restore)
├── logs/          # server log — attach to bug reports
├── global/        # cross-project memories (.md)
└── projects/
    └── <name>/    # per-project memories (.md)
```

## Files are the source of truth

Each memory is a **plain markdown file** with YAML frontmatter. The content of the
file is authoritative for *what the memory says*; `brain.db` is authoritative for
*metadata* (ids, tags, timestamps, embeddings, beliefs, version history).

```markdown
---
type: memory
title: Redis pub/sub fan-out choice
project: myapp
tags: ["redis", "sync"]
category: architecture
created: 2026-07-01T10:00:00+00:00
---

Fan-out via Redis pub/sub keeps p95 under budget — see [[#12]].
```

`type` is the one field required by the OKF spec ([[obsidian-okf]]); the rest are
wadachi's extensions.

## You may edit files by hand

It's a feature, not a hack. The parser is **tolerant**: missing frontmatter, an
unclosed `---`, tags in JSON or comma format — nothing breaks reading. If a file
drifts from canonical form, `wadachi doctor --fix` regenerates the frontmatter from
the database **without touching your prose**.

## The three wiki files

Following the LLM Wiki pattern ([[obsidian-okf]]):

- **`SCHEMA.md`** — the conventions of *your* brain. Created once by `wadachi init`,
  then never overwritten: edit it, extend it, make it yours. Agents read it.
- **`index.md`** — the generated catalog: one wikilinked line per memory, grouped by
  project. Regenerated automatically on every store/delete.
- **`log.md`** — append-only journal: `## [timestamp] op — detail` for every store,
  delete, merge, obsidian-links run. Grep it to answer "what happened last Tuesday?".

## brain.db, briefly

SQLite, one file, versioned schema. Tables: `memories`, `decisions`, `projects`,
`memory_versions` (every prior version of every edited memory), `beliefs` (the
epistemic envelope, [[beliefs]]), `insights`, `schema_version` (migrations,
[[safety]]). Embeddings are cached here as blobs so semantic search is instant.
