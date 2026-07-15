# get_context — start here, every session

The killer tool. One call at session start loads everything relevant, in a **dense,
pointer-based format** designed to cost ~400–600 tokens instead of thousands.

## What it returns

```
# wadachi · project: myapp · search: semantic
## memorie (rilevanza ↓)
#12 architecture ·0.81· CRDT merge strategy
#31 config ·0.77· Redis pub/sub fan-out
D3  decision ·0.74· Yjs over Automerge
## decisioni recenti
D7 2026-07-02 · SQLite, not Postgres
## da rivedere
#44 [temporal] past date next to a deadline
## il brain propone
💡 2 gruppi di memorie ridondanti da fondere → sleep()
stats: 104 mem · 21 dec · 6 prog
→ contenuto completo: expand_memory(ids=[…])
```

Every line is a **pointer**: id + category + relevance + title. Drill into anything
with `expand_memory(ids=[12, 31])`.

## Arguments

| arg | meaning |
|---|---|
| cwd | working directory → project auto-detection ([[projects]]) |
| task_description | what you're about to do → relevance-ranked memories |
| limit = 8 | max memory pointers |
| max_tokens = 600 | token budget — see below |
| format = "dense" | or `"json"` for the full verbose payload |

## The budget

`max_tokens` truncates **by relevance, never by age**: needs-review lines shrink
first, then decisions, then the least relevant memories. Header, stats and the
proposals always survive. This means you can call `get_context(max_tokens=300)` in a
tight context window and still get the essentials.

## The brain proposes

The section that makes wadachi feel alive. At every session start it may say:

- *"N insights await your judgement"* → `list_insights`, then accept/reject;
- *"last sleep found 2 merge groups"* → `sleep()` for details ([[sleep]]);
- *"sleep hasn't run in 9 days"* → run it (or let cron).

Rule 3 in action: the software proposes and explains; **nothing happens until you
decide**.
