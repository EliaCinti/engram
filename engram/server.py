"""
Brain MCP Server — persistent memory + semantic search for Claude Code / Desktop.

Tools:
  Memory:     store_memory, recall, get_memory, list_memories, update_memory, delete_memory
  Decisions:  store_decision, list_decisions
  Projects:   register_project, list_projects, detect_project
  Context:    get_context (auto-inject relevant memories for current task)
  Status:     brain_status
"""

import json
import os
import sys

# Add parent dir to path so imports work when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from engram.store import MemoryStore
from engram.search import SearchEngine

# ── Init ──────────────────────────────────────────────────────

brain_dir = os.environ.get("BRAIN_DIR", os.path.expanduser("~/.engram"))
store = MemoryStore(brain_dir)
search_engine = SearchEngine(store)

mcp = FastMCP(
    "engram",
    instructions="""You have access to a persistent Brain — a knowledge base that survives across sessions.

## How to use the Brain effectively:

1. **START of every session**: Call `get_context` with the current working directory to load relevant memories and decisions. This saves you from re-analyzing everything.

2. **BEFORE deep-diving into files**: Call `recall` with keywords about what you're about to do. The Brain may already have insights, patterns, or decisions from previous sessions.

3. **AFTER completing work**: Call `store_memory` to save:
   - Architecture decisions and WHY they were made
   - Patterns discovered in the codebase
   - Bugs found and how they were fixed
   - Configuration details that took time to figure out
   - Any insight that would save time if you had it at the start

4. **For decisions**: Use `store_decision` when making choices between alternatives. Record what you chose, why, and what you rejected. Future sessions will thank you.

5. **Projects**: Use `register_project` to associate directory paths with project names. Then `get_context` will automatically scope memories to the relevant project.

## Categories for memories:
- `architecture`: System design, patterns, structure decisions
- `bugfix`: Bugs found and their solutions
- `config`: Configuration, setup, environment details
- `pattern`: Code patterns, conventions, style rules
- `context`: General project context and background
- `reference`: API details, library usage, external docs
- `note`: General notes

## Golden rule: If you spent time figuring something out, store it. The 30 seconds to store a memory saves 5 minutes next session.
""",
)


# ── Memory Tools ──────────────────────────────────────────────


@mcp.tool()
def store_memory(
    content: str,
    title: str,
    project: str = "global",
    tags: list[str] | None = None,
    category: str = "note",
) -> str:
    """Store knowledge in the Brain for future sessions.

    Args:
        content: The information to remember (markdown supported).
        title: Short descriptive title for this memory.
        project: Project name (use 'global' for cross-project knowledge).
        tags: Keywords for easier retrieval (e.g. ["python", "fastapi", "auth"]).
        category: One of: architecture, bugfix, config, pattern, context, reference, note.
    """
    result = store.store_memory(content, title, project, tags, category)
    return json.dumps(result, indent=2)


@mcp.tool()
def recall(
    query: str,
    project: str | None = None,
    limit: int = 5,
) -> str:
    """Search the Brain semantically. Use this to find relevant memories before starting work.

    Args:
        query: Natural language query describing what you're looking for.
        project: Scope search to a specific project (None = search all).
        limit: Maximum number of results to return.
    """
    results = search_engine.search(query, project=project, limit=limit)
    if not results:
        mode = "semantic" if search_engine.semantic_available else "keyword"
        return json.dumps({
            "results": [],
            "message": f"No relevant memories found (search mode: {mode}). Consider storing useful information as you work.",
        })

    return json.dumps({
        "results": results,
        "search_mode": "semantic" if search_engine.semantic_available else "keyword",
        "count": len(results),
    }, indent=2)


@mcp.tool()
def get_memory(memory_id: int) -> str:
    """Retrieve the full content of a specific memory by its ID.

    Args:
        memory_id: The numeric ID of the memory to retrieve.
    """
    result = store.get_memory(memory_id)
    if result is None:
        return json.dumps({"error": f"Memory #{memory_id} not found."})
    return json.dumps(result, indent=2)


@mcp.tool()
def list_memories(
    project: str | None = None,
    category: str | None = None,
) -> str:
    """List all memories in the Brain, optionally filtered.

    Args:
        project: Filter by project name.
        category: Filter by category (architecture, bugfix, config, pattern, context, reference, note).
    """
    results = store.list_memories(project, category)
    return json.dumps({"memories": results, "count": len(results)}, indent=2)


@mcp.tool()
def update_memory(
    memory_id: int,
    content: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Update an existing memory's content or tags.

    Args:
        memory_id: The numeric ID of the memory to update.
        content: New content (replaces existing). Pass None to keep current content.
        tags: New tags (replaces existing). Pass None to keep current tags.
    """
    success = store.update_memory(memory_id, content, tags)
    if success:
        return json.dumps({"status": "updated", "id": memory_id})
    return json.dumps({"error": f"Memory #{memory_id} not found."})


@mcp.tool()
def delete_memory(memory_id: int) -> str:
    """Permanently delete a memory from the Brain.

    Args:
        memory_id: The numeric ID of the memory to delete.
    """
    success = store.delete_memory(memory_id)
    if success:
        return json.dumps({"status": "deleted", "id": memory_id})
    return json.dumps({"error": f"Memory #{memory_id} not found."})


# ── Decision Tools ────────────────────────────────────────────


@mcp.tool()
def store_decision(
    decision: str,
    rationale: str = "",
    alternatives: str = "",
    context: str = "",
    project: str = "global",
) -> str:
    """Log a decision for future reference. Invaluable for understanding past choices.

    Args:
        decision: What was decided.
        rationale: Why this choice was made.
        alternatives: What other options were considered and why they were rejected.
        context: Surrounding context that influenced the decision.
        project: Project this decision belongs to.
    """
    result = store.store_decision(decision, rationale, alternatives, context, project)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_decisions(
    project: str | None = None,
    limit: int = 20,
) -> str:
    """List recent decisions, optionally filtered by project.

    Args:
        project: Filter by project name.
        limit: Maximum number of decisions to return.
    """
    results = store.list_decisions(project, limit)
    return json.dumps({"decisions": results, "count": len(results)}, indent=2)


# ── Project Tools ─────────────────────────────────────────────


@mcp.tool()
def register_project(
    name: str,
    description: str = "",
    paths: list[str] | None = None,
) -> str:
    """Register a project so the Brain can auto-detect it from the working directory.

    Args:
        name: Short project identifier (e.g. 'feynotes', 'laplacebo').
        description: What this project is about.
        paths: Filesystem paths associated with this project (for auto-detection).
    """
    result = store.register_project(name, description, paths)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_projects() -> str:
    """List all registered projects."""
    results = store.list_projects()
    return json.dumps({"projects": results, "count": len(results)}, indent=2)


# ── Context Tool (the killer feature) ────────────────────────


@mcp.tool()
def get_context(
    cwd: str = "",
    task_description: str = "",
    limit: int = 8,
) -> str:
    """Auto-inject relevant context at the start of a session. Call this FIRST.

    Detects the current project from cwd, then returns:
    - Project info
    - Recent relevant memories
    - Recent decisions
    - Brain stats

    Args:
        cwd: Current working directory (for project auto-detection).
        task_description: Brief description of what you're about to do (improves relevance).
        limit: Max memories to include.
    """
    # Detect project
    project = None
    project_info = None
    if cwd:
        project = store.detect_project(cwd)
    if project:
        projects = store.list_projects()
        project_info = next((p for p in projects if p["name"] == project), None)

    context = {
        "project": project_info or {"name": project or "unknown", "note": "No project detected. Use register_project to set up project auto-detection."},
        "search_mode": "semantic" if search_engine.semantic_available else "keyword (install fastembed for semantic search)",
    }

    # Get relevant memories
    if task_description:
        search_results = search_engine.search(task_description, project=project, limit=limit)
        context["relevant_memories"] = search_results
    else:
        # Just get recent memories for this project
        memories = store.list_memories(project=project)
        context["recent_memories"] = memories[:limit]

    # Get recent decisions
    decisions = store.list_decisions(project=project, limit=5)
    context["recent_decisions"] = decisions

    # Stats
    context["stats"] = store.stats()

    return json.dumps(context, indent=2)


# ── Status Tool ───────────────────────────────────────────────


@mcp.tool()
def brain_status() -> str:
    """Check Brain health and statistics."""
    stats = store.stats()
    return json.dumps({
        "brain_dir": str(store.brain_dir),
        "search_mode": "semantic (fastembed)" if search_engine.semantic_available else "keyword (fastembed not installed)",
        "stats": stats,
        "projects": store.list_projects(),
    }, indent=2)


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
