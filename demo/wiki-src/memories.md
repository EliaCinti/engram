# Memories

The atom of wadachi. A memory = one markdown file + one index row.

## Anatomy

| field | meaning |
|---|---|
| content | markdown body — the knowledge itself. Supports [[graph|wikilinks]] |
| title | short and descriptive — it's what search results show |
| project | scope; `global` for cross-project knowledge ([[projects]]) |
| tags | keywords for retrieval |
| category | one of the seven below |

## The seven categories

| category | use for |
|---|---|
| architecture | system design, structure, high-level patterns |
| bugfix | bugs found and their solutions |
| config | setup, environment, infrastructure details |
| pattern | conventions, recurring code patterns, style rules |
| context | project background, goals, constraints |
| reference | API details, library usage, external docs |
| note | everything else |

## Storing well

```
store_memory(
  content  = "Gemini 504 in the fix loop → resume from checkpoint. See [[#63]].",
  title    = "Gemini 504 recovery in convert loop",
  project  = "pipeline",
  tags     = ["gemini", "504", "resume"],
  category = "bugfix")
```

Habits that pay off:

- **Store the moment you figure something out.** Thirty seconds now saves minutes in
  every future session.
- **Titles are for your future self** — "Fix" is useless; "Gemini 504 recovery in
  convert loop" is gold.
- **Link related memories** in the content (`[[#42]]` or `[[file-slug]]`): every link
  becomes a graph edge ([[graph]]).
- Record *choices* as [[decisions]], not memories — they carry rationale and
  alternatives.

## Updating: nothing is ever lost

`update_memory` replaces content and/or tags — but first it **snapshots the previous
version** into `memory_versions`. Retrieve the history with `memory_history(id)`;
this also powers [[time-travel]].

## Deleting vs retiring

`delete_memory` is permanent (file + row). It's almost never what you want: for
knowledge that stopped being true, prefer `flag_stale` — the memory stays,
recoverable, annotated in every recall ([[beliefs]]). Delete is for noise, stale is
for history.

## Access tracking

Reading a memory (`get_memory`, `expand_memory`) bumps its access counter and
timestamp. This feeds decay ([[beliefs]]): knowledge you actually use stays on top.
