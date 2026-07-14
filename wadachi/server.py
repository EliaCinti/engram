"""
Wadachi MCP Server — persistent memory + semantic search for Claude Code / Desktop.

Tools (25), grouped by area:
  Memory:       store_memory, get_memory, list_memories, update_memory, delete_memory, memory_history
  Search/Ctx:   recall, get_context, brain_status
  Decisions:    store_decision, list_decisions
  Projects:     register_project, list_projects
  Constellation: recall_associative, related_memories, memory_graph, rebuild_entity_graph
  Beliefs:      review_beliefs, set_belief, flag_stale
  Reflection:   reflect, list_insights, accept_insight, reject_insight
  Procedural:   review_procedures
"""

import functools
import json
import os
import sys
import time

# Add parent dir to path so imports work when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from wadachi import __version__
from wadachi.log import setup as _log_setup
from wadachi.store import MemoryStore
from wadachi.search import SearchEngine
from wadachi.graph import MemoryGraph
from wadachi.entities import EntityGraph
from wadachi.beliefs import BeliefReviewer
from wadachi.reflect import Reflector
from wadachi.procedural import ProceduralReviewer

# ── Init ──────────────────────────────────────────────────────

# default: ~/.wadachi, ma se esiste un brain legacy in ~/.engram continua a usarlo
_legacy_brain = os.path.expanduser("~/.engram")
_default_brain = _legacy_brain if os.path.isdir(_legacy_brain) else os.path.expanduser("~/.wadachi")
brain_dir = os.environ.get("BRAIN_DIR", _default_brain)
log = _log_setup(brain_dir)
store = MemoryStore(brain_dir)
search_engine = SearchEngine(store)
log.info("wadachi %s — brain: %s, search: %s", __version__, brain_dir,
         "semantic" if search_engine.semantic_available else "keyword")


def _instrumented(fn):
    """Ogni tool loggato: durata a DEBUG, eccezioni con traceback a ERROR.

    Le eccezioni vengono ri-alzate (il protocollo MCP le riporta al client);
    il log su file è ciò che l'utente può allegare a una segnalazione.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            out = fn(*args, **kwargs)
            log.debug("tool %s ok (%.0f ms)", fn.__name__, (time.perf_counter() - t0) * 1000)
            return out
        except Exception:
            log.exception("tool %s FALLITO (args=%r kwargs=%r)", fn.__name__, args, kwargs)
            raise
    return wrapper


def tool(*dargs, **dkwargs):
    """Come @mcp.tool(), ma con logging trasparente."""
    def deco(fn):
        return mcp.tool(*dargs, **dkwargs)(_instrumented(fn))
    return deco

mcp = FastMCP(
    "wadachi",
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


@tool()
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


@tool()
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
    results = _annotate_beliefs(results)
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


@tool()
def get_memory(memory_id: int) -> str:
    """Retrieve the full content of a specific memory by its ID.

    Args:
        memory_id: The numeric ID of the memory to retrieve.
    """
    result = store.get_memory(memory_id)
    if result is None:
        return json.dumps({"error": f"Memory #{memory_id} not found."})
    return json.dumps(result, indent=2)


@tool()
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


@tool()
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


@tool()
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


@tool()
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


@tool()
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


@tool()
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


@tool()
def list_projects() -> str:
    """List all registered projects."""
    results = store.list_projects()
    return json.dumps({"projects": results, "count": len(results)}, indent=2)


# ── Context Tool (the killer feature) ────────────────────────


@tool()
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

    # Beliefs needing review (so a session opens knowing what's stale)
    try:
        context["needs_review"] = BeliefReviewer(store).scan(project=project, limit=5)
    except Exception:  # noqa: BLE001 — review is best-effort, never block context
        context["needs_review"] = []

    # Stats
    context["stats"] = store.stats()

    return json.dumps(context, indent=2)


# ── Status Tool ───────────────────────────────────────────────


@tool()
def brain_status() -> str:
    """Check Brain health and statistics."""
    stats = store.stats()
    return json.dumps({
        "brain_dir": str(store.brain_dir),
        "search_mode": "semantic (fastembed)" if search_engine.semantic_available else "keyword (fastembed not installed)",
        "stats": stats,
        "projects": store.list_projects(),
    }, indent=2)


# ── Constellation: graph-aware recall (the differentiator) ───


def _assoc_graph(project: str | None) -> MemoryGraph:
    """Build the memory graph (citations + semantic kNN), enriched with the
    cached Graphify entity edges if an entity graph has been built."""
    g = MemoryGraph(store).build(project)
    eg = EntityGraph(store)
    if eg.graph_json.exists():
        try:
            g.load_entity_edges(str(eg.graph_json))
        except Exception:  # noqa: BLE001 — entity enrichment is best-effort
            pass
    return g


@tool()
def recall_associative(query: str, project: str | None = None, limit: int = 5) -> str:
    """Spreading-activation recall over the memory graph (HippoRAG-style).

    Unlike `recall` (pure cosine top-k), this seeds the query's best matches and
    propagates activation along citation, semantic, and shared-entity edges, so
    strongly-connected memories surface even when not textually similar. Returns
    the associative ranking AND the plain-cosine baseline for comparison.

    Args:
        query: Natural language query.
        project: Scope to a project (None = whole brain).
        limit: Number of results.
    """
    g = _assoc_graph(project)
    try:
        return json.dumps(g.associative_recall(query, limit=limit), indent=2)
    except RuntimeError as e:
        # senza fastembed il recall associativo non può embeddare la query:
        # niente crash MCP — errore chiaro + fallback keyword utilizzabile
        return json.dumps({
            "error": str(e),
            "hint": "recall_associative richiede la ricerca semantica: pip install 'wadachi[semantic]'.",
            "keyword_fallback": json.loads(recall(query, project=project, limit=limit)),
        }, indent=2)


@tool()
def related_memories(memory_id: int, limit: int = 8) -> str:
    """Show the memories most strongly linked to a given one (typed neighbours).

    Args:
        memory_id: The memory to expand from.
        limit: Max neighbours to return.
    """
    g = _assoc_graph(None)
    return json.dumps({"id": memory_id, "related": g.related(memory_id, limit)}, indent=2)


@tool()
def memory_graph(project: str | None = None, focus_id: int | None = None,
                 include_entities: bool = True) -> str:
    """Overview of the brain as a graph: hubs, orphans, components, a Mermaid
    diagram of the citation backbone, and (if built) the Graphify entity graph
    with communities, god-nodes and surprising connections.

    Args:
        project: Scope to a project (None = whole brain).
        focus_id: If set, the Mermaid diagram is centred on this memory.
        include_entities: Include the Graphify entity-graph summary.
    """
    g = _assoc_graph(project)
    out = g.stats()
    out["mermaid"] = g.to_mermaid(focus=focus_id)
    if include_entities:
        out["entity_graph"] = EntityGraph(store).summary()
    return json.dumps(out, indent=2)


@tool()
def rebuild_entity_graph(project: str | None = None) -> str:
    """(Re)build the Graphify entity knowledge graph over the brain.

    Runs extraction via the local `claude` CLI (free; uses your Claude plan).
    Requires `graphifyy` installed (pip install graphifyy). Cached under
    BRAIN_DIR/.constellation so other tools read it instantly.
    """
    return json.dumps(EntityGraph(store).rebuild(), indent=2)


@tool()
def memory_history(memory_id: int) -> str:
    """Show prior versions of a memory (preserved on every update — non-destructive).

    Args:
        memory_id: The memory whose edit history to retrieve.
    """
    return json.dumps({"id": memory_id, "history": store.get_memory_history(memory_id)}, indent=2)


# ── Belief revision (Phase 2) ────────────────────────────────


def _annotate_beliefs(results: list[dict]) -> list[dict]:
    """Attach belief status to memory results and hide retired ones. Additive."""
    out = []
    for r in results:
        if r.get("type") == "memory":
            b = store.get_belief(r["id"])
            if b["status"] == "retired":
                continue
            if b["status"] != "active" or b["superseded_by"] or b["confidence"] < 0.7:
                note = {"status": b["status"], "confidence": b["confidence"]}
                if b["superseded_by"]:
                    note["superseded_by"] = b["superseded_by"]
                if b["review_reason"]:
                    note["reason"] = b["review_reason"]
                r["belief"] = note
        out.append(r)
    return out


@tool()
def review_beliefs(project: str | None = None) -> str:
    """Scan the brain for memories that have likely gone stale and need review:
    superseded by a newer memory, past a temporal deadline, conditional/provisional,
    or already flagged. Read-only — it suggests, never deletes. Confirm with flag_stale.

    Args:
        project: Scope to a project (None = whole brain).
    """
    flagged = BeliefReviewer(store).scan(project=project)
    return json.dumps({"flagged": flagged, "count": len(flagged)}, indent=2)


@tool()
def set_belief(memory_id: int, confidence: float | None = None, status: str | None = None,
               valid_until: str | None = None, review_reason: str | None = None,
               superseded_by: int | None = None) -> str:
    """Update a memory's belief envelope. None args keep the current value.

    Args:
        memory_id: The memory.
        confidence: 0..1 how sure we are.
        status: active | stale | retired.
        valid_until: ISO date after which the claim expires.
        review_reason: why the status/confidence changed.
        superseded_by: id of the memory that replaced this one.
    """
    return json.dumps(store.set_belief(memory_id, confidence=confidence, status=status,
                                       valid_until=valid_until, review_reason=review_reason,
                                       superseded_by=superseded_by), indent=2)


@tool()
def flag_stale(memory_id: int, reason: str, superseded_by: int | None = None) -> str:
    """Mark a memory as stale: kept and recoverable, but annotated in recall.

    Args:
        memory_id: The memory to flag.
        reason: Why it's stale.
        superseded_by: id of the memory that replaced it, if any.
    """
    return json.dumps(store.set_belief(memory_id, status="stale", review_reason=reason,
                                       superseded_by=superseded_by), indent=2)


# ── Reflection & procedural (Phase 3) ────────────────────────


@tool()
def reflect(project: str | None = None, limit: int = 15, store_them: bool = True) -> str:
    """Think across memories: surface cross-project analogies and non-obvious
    connections that recall cannot reach (reuses the Graphify graph — no extra LLM
    cost). Candidates are saved as `proposed` insights (unless store_them=False)
    for you to accept_insight / reject_insight.

    Args:
        project: Scope to a project (None = whole brain).
        limit: Max candidates.
        store_them: Persist candidates as proposed insights.
    """
    cands = Reflector(store).candidates(project=project, limit=limit)
    saved = [store.store_insight(c["claim"], c["itype"], c["evidence_ids"]) for c in cands] if store_them else []
    return json.dumps({"candidates": cands, "stored": len(saved), "count": len(cands)}, indent=2)


@tool()
def list_insights(status: str | None = "proposed") -> str:
    """List reflection insights, optionally by status (proposed | accepted | rejected)."""
    items = store.list_insights(status=status)
    return json.dumps({"insights": items, "count": len(items)}, indent=2)


@tool()
def accept_insight(insight_id: int, project: str = "global") -> str:
    """Accept an insight: mark it accepted and promote it to a real memory linked
    to its source memories.

    Args:
        insight_id: The insight to accept.
        project: Project for the promoted memory.
    """
    ins = store.get_insight(insight_id)
    if not ins:
        return json.dumps({"error": f"Insight #{insight_id} not found."})
    store.set_insight_status(insight_id, "accepted")
    refs = " ".join(f"[[#{m}]]" for m in ins["evidence_ids"])
    mem = store.store_memory(
        content=f"{ins['claim']}\n\nDeriva da: {refs}",
        title=f"Insight: {ins['claim'][:60]}",
        project=project, tags=["insight", ins["itype"]], category="context")
    return json.dumps({"status": "accepted", "insight_id": insight_id, "memory": mem}, indent=2)


@tool()
def reject_insight(insight_id: int) -> str:
    """Reject an insight (kept on record, marked rejected).

    Args:
        insight_id: The insight to reject.
    """
    ok = store.set_insight_status(insight_id, "rejected")
    return json.dumps({"status": "rejected" if ok else "not_found", "insight_id": insight_id})


@tool()
def review_procedures(project: str | None = None) -> str:
    """Find recurring-incident clusters and propose always-on rules for review.
    Read-only — never edits your operating instructions.

    Args:
        project: Scope to a project (None = whole brain).
    """
    rules = ProceduralReviewer(store).review(project=project)
    return json.dumps({"candidate_rules": rules, "count": len(rules)}, indent=2)


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
