# Search & retrieval

Three retrieval modes, one philosophy: show your work.

## recall — the everyday search

```
recall("how do we handle rate limits?", project="myapp", limit=5)
```

Semantic search over memories *and* decisions (or keyword matching without the
`[semantic]` extra — same API, honest downgrade). Results carry:

- `score` — similarity, already adjusted for decay ([[beliefs]]);
- `belief` — annotation if the memory is stale/superseded/low-confidence;
- `scope` — project vs global evidence ([[projects]]);
- `decay` — if ranking was reduced by staleness, you see by how much.

## recall(neighbors=true) — graph-aware search

Each result also brings its **strongest typed graph neighbours** (1 hop): what's
*connected* surfaces even when it isn't textually similar. The neighbour list shows
the relation (`cites`, `supersedes`, `similar`…), so you know *why* it appeared.

## recall_associative — spreading activation

The deep cut. Your query's best matches become seeds; activation spreads along
citation, semantic and entity edges (personalized PageRank). Memories strongly
connected to the topic emerge even with zero textual overlap. The response includes
the plain-cosine baseline **so the difference is auditable** — you can see exactly
what the graph added.

## expand_memory — from pointer to content

Dense results are pointers by design. `expand_memory(ids=[12, 31, 44])` returns full
contents in one call (max 10), and counts as an access — rejuvenating those memories
against decay.

## Semantic vs keyword

| | semantic (fastembed) | keyword |
|---|---|---|
| finds by | meaning | token overlap |
| install | `wadachi[semantic]` | built-in |
| cost | $0, local model | $0 |
| speed | ~50ms | ~5ms |

`brain_status` tells you which mode is active. Everything else — beliefs, graph
citations, scoping, decay — works identically in both.
