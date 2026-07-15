# Sleep — consolidation, proposed

Biological brains consolidate memories during sleep. Wadachi does the same — with
one difference that defines the product: **it only proposes**.

## Running it

```bash
wadachi sleep          # CLI — perfect in cron/launchd
```

or the `sleep()` tool from your agent. Read-only, always.

## What it finds

1. **Merge candidates** — the graph is clustered into communities (label
   propagation, pure Python); communities whose memories are semantic
   near-duplicates become groups proposed for fusion. A finished project's twenty
   progress notes begging to become one synthesis — that's what this catches.
2. **Decay candidates** — leaves with **no explicit links** (semantic edges don't
   count: they're automatic), never recalled, past the decay threshold.
   Candidates for `flag_stale`.
3. **Orphans** — nodes with no connections at all. Candidates for linking.

## What happens next

Nothing — until you act. The report is cached, and your **next [[get-context]]
proposes it**: *"💡 last sleep found 2 merge groups → sleep() for details"*.

To consolidate: **you** (or your agent, with your approval) write the synthesis,
then

```
merge_memories(source_ids=[45,46,47], title="...", content="<your synthesis>")
```

The new memory carries automatic `[[#id]]` provenance links; sources are marked
superseded — recoverable forever, annotated in recall ([[beliefs]]).

## Scheduling it

Sleep is designed for cron. Weekly is plenty for most brains:

```
0 4 * * 0  BRAIN_DIR=$HOME/.wadachi /path/to/wadachi sleep
```

Monday morning, get_context greets you with what the weekend's sleep dreamed up.
