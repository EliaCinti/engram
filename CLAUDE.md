# Wadachi — Session Rules

You have access to **Wadachi**, a persistent memory system via MCP. Use it.

## Session Start (MANDATORY)
1. Call `get_context` with the current working directory and a brief task description.
2. Read the returned memories and decisions before touching any files.
3. If you see relevant memories, use `get_memory` to load full content when needed.

## During Work
- Before investigating something: call `recall` first — you might already know it.
- When you figure something out (a bug, a pattern, a config quirk): call `store_memory` immediately.
- When choosing between approaches: call `store_decision` with rationale and rejected alternatives.

## Session End
- Store anything you learned that would help a fresh session start faster.
- Architecture changes, new patterns, gotchas, and environment details are especially valuable.

## Memory Categories
Use the right category for better retrieval:
- `architecture` — system design, structure, patterns
- `bugfix` — bugs found + solutions
- `config` — setup, env vars, infrastructure
- `pattern` — code conventions, recurring patterns
- `context` — general project background
- `reference` — API details, library notes
- `note` — everything else

## Tags
Always include 3-5 relevant tags when storing memories. Think: what words would you search for to find this again?

## Project Scoping
If `get_context` detects a project, scope your `store_memory` and `store_decision` calls to that project name.
If no project is detected, use `register_project` to set one up.
