# LLM Wiki, Obsidian & OKF

Wadachi doesn't invent a storage religion — it adopts the emerging standards and
adds what they lack.

## The LLM Wiki pattern

Karpathy's pattern (April 2026): agent memory as a **maintained markdown wiki** —
raw sources → wiki pages with `[[wikilinks]]` → a schema file with the conventions;
plus an `index.md` catalog and an append-only `log.md`. Wadachi's brain *is* this
pattern ([[brain]]): the wiki layer is `global/` + `projects/`, the schema file is
`SCHEMA.md` (created by init, then yours), index and log are maintained on every
write.

What wadachi adds on top is the cognitive cycle the pattern lacks: [[beliefs]],
[[decisions|provenance]], [[time-travel]], [[sleep]].

## Obsidian: format, not dependency

The brain dir is a **valid Obsidian vault** — open it and you get reading,
searching, and the graph view for free. Zero lock-in either way: wadachi never
requires Obsidian; Obsidian needs nothing from wadachi.

One catch: prose references like "memory #42" and `[[#42]]` are edges in *wadachi's*
graph, but Obsidian only resolves `[[file-name]]` links. Hence:

```bash
wadachi obsidian --dry-run    # see what would change
wadachi obsidian              # generate the links
```

**Explicitly on demand — never automatic.** It appends a marked `Links:` section
with `[[slug]]` wikilinks to files that reference other memories by id. Prose
untouched, every change versioned, embeddings invalidated for reindexing,
idempotent. Your Obsidian graph lights up.

## OKF — Open Knowledge Format

Google's vendor-neutral spec (2026) for agent knowledge: a directory of markdown
files with YAML frontmatter, `type` as the only required field, tolerant consumers.
Every wadachi memory file carries `type: memory` — **your brain is a conformant OKF
bundle** as it sits on disk. Any OKF consumer can read it; `wadachi doctor --fix`
upgrades pre-OKF brains in place.

Portability in every direction is the point: markdown for humans, vault for
Obsidian, bundle for OKF, [[safety|export]] for everything at once.
