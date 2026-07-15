# The typed knowledge graph

Not a visualization — a data structure the system *uses*. Recall walks it,
provenance queries it, sleep clusters it.

## Nodes

- **Memories** — `#42`
- **Decisions** — `D7`, first-class citizens ([[decisions]])

## Edges

| kind | how it forms | notes |
|---|---|---|
| citation | you write a link (see below) | typed: updates / contradicts / cites / relates |
| supersedes | belief supersession ([[beliefs]]) | weight 1.5, the strongest signal |
| semantic | nearest-neighbour similarity | automatic, the background tissue |
| entity | shared entities (optional, Graphify) | `rebuild_entity_graph`, local claude CLI, $0 |

## How citations are written

All of these create edges — use whichever reads naturally:

```
[[file-slug]]            wikilink, Obsidian-compatible
[[file-slug|shown text]] wikilink with alias
[[#42]]                  memory by id
[[D7]]                   decision by id
"see memory #42"         plain prose (English or Italian)
"as per decision #7"     plain prose
```

The relation type is inferred from surrounding words: "updates/supersedes…" →
*updates*; "contradicts/smentisce…" → *contradicts*; "see/cfr…" → *cites*;
otherwise *relates*.

> **Link generously.** Every link is an edge; every edge makes associative recall,
> `why`, and sleep smarter. The graph is only as good as your linking habit — and
> the server instructs agents to build it as they store.

## What runs on the graph

- **recall_associative** — spreading activation (personalized PageRank) from your
  query's seeds ([[search]]);
- **why** — decision provenance via in-edges ([[time-travel]]);
- **communities** — label propagation clustering for [[sleep]];
- **related_memories / memory_graph** — introspection: strongest neighbours, hubs,
  orphans, typed edge counts, a Mermaid diagram of the citation backbone.

## The local visualizer

```bash
python -m wadachi.web        # http://localhost:8420
```

The full brain as an interactive D3 graph: project clusters, decisions as diamonds,
supersedes edges in vermilion, an **"as of" time slider** (temporal dimension), and
click-through provenance on every decision. Local only — never exposed.
