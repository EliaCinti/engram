# Consolidation, insights & procedures

Three mechanisms that turn accumulation into understanding — all of them proposals.

## consolidate — similarity groups on demand

```
consolidate(project="myapp", threshold=0.86)
```

Finds groups of near-duplicate **active** memories by embedding similarity
(read-only). Complementary to [[sleep]]: sleep clusters by *graph structure*,
consolidate by *pure similarity*. Both feed the same action:

## merge_memories — the human synthesis

```
merge_memories(
  source_ids = [45, 46, 51],
  title      = "CEM project — final synthesis",
  content    = "<the synthesis YOU wrote>")
```

- The synthesis is stored as a new memory with automatic provenance links
  (`Consolida: [[#45]] [[#46]] [[#51]]`) — graph edges included.
- Sources become `stale` + `superseded_by` the new memory: out of the way in
  recall, never gone, always recoverable.

Wadachi will never write the synthesis for you silently — the understanding step is
deliberately human (or agent-with-approval).

## reflect — cross-memory insights

```
reflect(project=None)
```

Thinks *across* memories: surfaces analogies and non-obvious connections that no
single memory holds (reusing the entity graph — no LLM cost). Candidates are stored
as **proposed insights**:

- `list_insights()` — review the queue (also surfaced by [[get-context]]);
- `accept_insight(id)` — promotes it to a real memory linked to its evidence;
- `reject_insight(id)` — kept on record as rejected, never re-proposed.

## review_procedures — from incidents to rules

Recurring incidents (tagged bugfix/drift/anti-pattern…) are clustered by theme; each
recurring theme becomes a **candidate always-on rule** — the brain learning not just
facts but *how to act*. Read-only: it drafts the rule, you decide whether it enters
your CLAUDE.md or SCHEMA.md.
