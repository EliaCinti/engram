# Projects & scoping

Projects keep knowledge from different worlds apart — and declare it when it crosses.

## Registering

```
register_project(
  name        = "myapp",
  description = "The realtime sync engine",
  paths       = ["/Users/you/code/myapp"])
```

Paths power **auto-detection**: when `get_context(cwd=...)` is called from anywhere
inside a registered path (subdirectories included), the project is detected and the
context scoped automatically. One project can register several paths.

## What scoping means

A search scoped to project `myapp` sees:

- memories of `myapp`, **plus**
- memories of `global` — the cross-cutting knowledge every project shares.

## Evidence scoping

Scoped results **declare where each piece of evidence comes from**: every memory in
a scoped recall carries `scope: "project"` or `scope: "global"`. When your agent
reasons from retrieved memories, it can tell project-specific facts from general
rules — projects never silently contaminate each other's inferences. This is an
open problem in the LLM-wiki ecosystem; wadachi's answer is to make provenance
explicit rather than pretend isolation.

## global: use it deliberately

`global` is for knowledge that is *genuinely* cross-project: your dev environment,
personal conventions, reusable gotchas ("Docker bind-mounts break on rename").
Project-specific details stored in `global` pollute every other project's context —
when in doubt, scope to the project.

## The graph respects scope too

`recall_associative`, `memory_graph`, [[sleep]] — all accept a `project` argument
and build the graph over that scope only.
