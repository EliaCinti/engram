# Provenance & time-travel

Two questions ordinary stores can't answer. Wadachi can, because it never throws
anything away.

## why — interrogating decisions

```
why("why do we use pandoc for the pdfs?")
```

Searches [[decisions]], returns for each match:

| field | content |
|---|---|
| decided | what was chosen |
| why | the rationale, verbatim from when it was fresh |
| rejected_alternatives | what you gave up, and why |
| context | the situation at the time |
| when | date |
| cited_by | memories referencing this decision — graph evidence |

The last field is the special one: it's walked from the typed [[graph]], so you see
not just the decision but **its footprint** in your knowledge.

## as_of — the brain at a past date

```
as_of("2026-03-01", query="deploy pipeline")
```

Returns memories that **existed on that date**, each with:

- `status_at_date` — active · *already superseded by #N* (if the successor existed
  by then) · *expired* (past its valid-until);
- `content_as_of` — the content **as it was on that date**, reconstructed from the
  non-destructive version history ([[memories]]).

Ask "what did we believe in March?" and get March's answer — not today's memories
cosplaying as March's.

## Why this works

Three mechanisms compound: every update snapshots the previous version; supersession
is a dated, typed edge instead of a deletion; and beliefs carry validity windows.
History isn't a backup you restore — it's a dimension you query.
