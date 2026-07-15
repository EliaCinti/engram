# Safety — the whole chain

The second design rule: **memories are sacred**. This page is every mechanism that
enforces it, end to end. There are no gaps in this chain by design.

## 1 · Migrations with automatic backup

Schema changes ship as numbered migration scripts. On first start after an upgrade:
`brain.db` is **copied to `backups/` first**, then each migration runs in its own
transaction — a failure rolls back and names the backup. Legacy databases (including
the Engram era) are adopted by an idempotent baseline that never touches data.

## 2 · Non-destructive updates

Every `update_memory` snapshots the previous version (`memory_versions`). Nothing is
overwritten, ever — this powers `memory_history` and [[time-travel]].

## 3 · Nothing cognitive is destructive

Stale ≠ deleted ([[beliefs]]). Merged sources are superseded, not erased
([[consolidation]]). Rejected insights are kept as rejected. The only permanent
operation in the whole product is an explicit `delete_memory`.

## 4 · export — the portable snapshot

```bash
wadachi export                    # → wadachi-export-<timestamp>.tar.gz
```

The entire brain (markdown + db + schema/index/log) with a `MANIFEST.json`
(version, counts, schema). **Strictly read-only**: no migrations run, the brain is
byte-identical after — verified by test. This is what makes the cautious upgrade
path possible:

> **Coming from Engram?** Install wadachi → `wadachi export` immediately (nothing
> has migrated yet) → archive somewhere safe → then let init/doctor migrate with
> their own backups. Belt, suspenders, and a second belt.

## 5 · restore — both directions of time

```bash
wadachi restore <archive> --to <new-dir>     # inspect a snapshot on the side
wadachi restore <archive> --replace          # "restart from here" on the active brain
```

`--replace` swaps the live brain with the archive — but **first it safety-exports
the current state** to `backups/pre-restore-<ts>.tar.gz`. Even going back in time is
reversible: restore the safety export to return to the present.

## 6 · Session backups (optional)

A Stop-hook (or any scheduler) can run a bundled script that tars the brain at every
session end with rotation. Cheap insurance on top of everything above.

## The philosophy, stated once

Trust in a memory system is earned by the exit, not the entrance. Plain files you
own, snapshots you can take before anything changes, restores that are themselves
reversible, and zero telemetry watching any of it.
