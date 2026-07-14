"""
Regression tests for the Constellation layer + non-destructive updates.
Hermetic: runs against a throwaway BRAIN_DIR. No pytest needed.

    python tests/test_constellation.py     # exits 1 on failure
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wadachi.store import MemoryStore          # noqa: E402
from wadachi.graph import MemoryGraph          # noqa: E402

PASS = FAIL = 0


def ok(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  ✗ FAIL: {name}")


def main() -> int:
    td = tempfile.mkdtemp()
    s = MemoryStore(td)
    s.store_memory("Contenuto A. Vedi memoria #2 per i dettagli.", "Memo A")
    s.store_memory("Aggiorna memoria #1 con dati nuovi.", "Memo B")
    c = s.store_memory("Una nota isolata su tutt'altro argomento.", "Memo C")
    # ids: A=1, B=2, C=3

    # ── non-destructive update_memory (use C; leave A/B intact for graph tests) ──
    s.update_memory(c["id"], content="C versione 2")
    s.update_memory(c["id"], content="C versione 3")
    hist = s.get_memory_history(c["id"])
    ok("update preserves 2 versions", len(hist) == 2)
    ok("current content is latest", s.get_memory(c["id"])["content"] == "C versione 3")
    ok("oldest version recoverable",
       hist[-1]["content"].split("---")[-1].strip() == "Una nota isolata su tutt'altro argomento.")

    # ── citation graph + typed edges ──
    g = MemoryGraph(s).build()
    cit = {(e.src, e.dst, e.rel) for e in g.edges if e.kind == "citation"}
    ok("A cites #2", (1, 2, "cites") in cit)
    ok("B 'updates' #1 (typed)", (2, 1, "updates") in cit)

    # ── stats reports all edge kinds ──
    st = g.stats()
    ok("stats has edge-kind counts",
       {"citation_edges", "semantic_edges", "entity_edges"} <= set(st))

    # ── related() dedupes neighbours ──
    ids = [r["id"] for r in g.related(1)]
    ok("related() has no duplicate neighbours", len(ids) == len(set(ids)))

    # ── associative recall returns both rankings ──
    r = g.associative_recall("contenuto A", limit=2)
    ok("associative_recall returns associative+baseline",
       "associative" in r and "baseline_cosine" in r)

    # ── entity-edge bridge (synthetic Graphify graph.json) ──
    fa = s.get_memory(1)["filepath"].replace("/", "__")
    fc = s.get_memory(3)["filepath"].replace("/", "__")
    gj = os.path.join(td, "g.json")
    json.dump({"nodes": [
        {"id": "e1", "file_type": "concept", "label": "SharedX", "source_file": None},
        {"id": "dA", "file_type": "document", "source_file": fa},
        {"id": "dC", "file_type": "document", "source_file": fc}],
        "links": [{"source": "dA", "target": "e1"}, {"source": "dC", "target": "e1"}]},
        open(gj, "w"))
    added = g.load_entity_edges(gj)
    ok("entity bridge adds edge", added >= 1)
    ok("A and C linked via shared entity",
       any(e.kind == "entity" and {e.src, e.dst} == {1, 3} for e in g.edges))

    # ── belief revision ──
    from wadachi.beliefs import BeliefReviewer
    ok("belief defaults (active, 0.7)",
       s.get_belief(1)["status"] == "active" and s.get_belief(1)["confidence"] == 0.7)
    s.set_belief(2, status="stale", review_reason="test")
    ok("set_belief persists", s.get_belief(2)["status"] == "stale")
    flagged = BeliefReviewer(s).scan()
    sup = [f for f in flagged if f["memory_id"] == 1 and "superseded" in f["signals"]]
    ok("scanner flags #1 superseded by #2", bool(sup) and sup[0]["superseded_by"] == 2)

    # ── reflection: insights store + smoke ──
    from wadachi.reflect import Reflector
    ins = s.store_insight("claim X", "surprising_connection", [1, 3])
    ok("insight stored as proposed", any(i["id"] == ins["id"] for i in s.list_insights("proposed")))
    s.set_insight_status(ins["id"], "accepted")
    ok("insight status updated", s.get_insight(ins["id"])["status"] == "accepted")
    ok("reflect() returns a list", isinstance(Reflector(s).candidates(), list))

    # ── procedural: recurring-incident clustering ──
    from wadachi.procedural import ProceduralReviewer
    s.store_memory("Duplicato lezione 38 creato per errore.", "Dup lez38", tags=["duplicato"], category="bugfix")
    s.store_memory("Duplicato lezione 28 creato di nuovo.", "Dup lez28", tags=["duplicato"], category="bugfix")
    rules = ProceduralReviewer(s).review()
    dup = [r for r in rules if r["theme"] == "duplicato"]
    ok("procedural finds recurring 'duplicato' cluster", bool(dup) and dup[0]["recurrence"] >= 2)

    print("\n" + "=" * 56)
    print(f"CONSTELLATION TESTS: {PASS} passed, {FAIL} failed")
    print("=" * 56)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())


def test_constellation_suite():
    """Pytest shim: esegue l'intera suite storica (richiede embeddings)."""
    import pytest
    from wadachi import search
    if not search._FASTEMBED_AVAILABLE:
        pytest.skip("richiede fastembed (ricerca semantica)")
    assert main() == 0
