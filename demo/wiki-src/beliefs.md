# Beliefs, staleness & decay

The heart of wadachi's epistemology: **a stored sentence is not a fact forever**.

## The belief envelope

Every memory carries:

| field | meaning |
|---|---|
| confidence | 0–1, how much to trust it (default 0.7) |
| status | `active` · `stale` · `retired` |
| valid_until | optional ISO date after which the claim expires |
| superseded_by | id of the memory that replaced it |
| review_reason | why the status changed |

## review_beliefs — the read-only scan

Flags memories that have *likely* gone stale:

- **superseded** — a newer memory replaced them;
- **temporal** — a past date sits next to deadline-ish wording ("resets July 1");
- **conditional** — provisional phrasing ("for now", "until we migrate").

It never changes anything. Findings appear in every [[get-context]] under
*needs review*; you confirm with `flag_stale` or `set_belief`.

## Supersession is structure

`flag_stale(42, reason="replaced", superseded_by=57)` doesn't bury memory #42 — it
draws a typed **supersedes** edge from #57 to #42 in the [[graph]]. Contradiction
over time becomes something you can *walk*: [[time-travel]] uses it to answer "what
was true in March?".

## Recall honesty

Stale and low-confidence memories still appear in results (retired ones don't), but
**annotated**: `belief: { status: "stale", superseded_by: 57, reason: ... }`. Your
agent opens a session knowing what it can no longer trust — instead of confidently
repeating last month's truth.

## Decay — gentle forgetting

Memories never recalled slowly lose ranking priority: **−2% per idle month past the
first, capped at −12%**, transparently reported as a `decay` field. Any access
(get/expand) rejuvenates them.

Deliberately gentle: decay **reorders, it never buries**. A perfect semantic match
still wins; among equals, the knowledge you actually use comes first. The fading
leaves feed [[sleep]]'s decay-candidates report — retirement is still your call.
