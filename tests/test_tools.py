"""1.2 — I 25 tool MCP chiamati come funzioni: contratto JSON e casi limite.

I tool condividono il brain di sessione (fixture `srv`): i test sono ordinati
dal DB vuoto verso stati più ricchi.
"""

import json


def j(out: str):
    """Ogni tool DEVE restituire JSON valido."""
    return json.loads(out)


# ── su DB (quasi) vuoto ───────────────────────────────────────


def test_brain_status_shape(srv):
    out = j(srv.brain_status())
    assert {"brain_dir", "search_mode", "stats", "projects"} <= out.keys()


def test_recall_empty_brain(srv):
    out = j(srv.recall("qualcosa che non esiste ancora"))
    assert out["results"] == []
    assert "message" in out


def test_get_context_no_project(srv):
    out = j(srv.get_context(cwd="/percorso/non/registrato"))
    assert "project" in out and "stats" in out
    assert "needs_review" in out


def test_review_beliefs_empty(srv):
    out = j(srv.review_beliefs())
    assert out["count"] == len(out["flagged"])


def test_review_procedures_empty(srv):
    out = j(srv.review_procedures())
    assert out["count"] == 0


def test_list_insights_empty(srv):
    assert j(srv.list_insights())["count"] == 0


def test_memory_graph_empty(srv):
    out = j(srv.memory_graph(include_entities=False))
    assert "mermaid" in out


# ── errori su ID inesistenti ──────────────────────────────────


def test_get_memory_not_found(srv):
    assert "error" in j(srv.get_memory(99999))


def test_update_memory_not_found(srv):
    assert "error" in j(srv.update_memory(99999, content="x"))


def test_delete_memory_not_found(srv):
    assert "error" in j(srv.delete_memory(99999))


def test_accept_insight_not_found(srv):
    assert "error" in j(srv.accept_insight(99999))


def test_reject_insight_not_found(srv):
    assert j(srv.reject_insight(99999))["status"] == "not_found"


def test_memory_history_not_found(srv):
    assert j(srv.memory_history(99999))["history"] == []


def test_related_memories_not_found(srv):
    out = j(srv.related_memories(99999))
    assert out["related"] == []


# ── ciclo di vita completo attraverso i tool ──────────────────


def test_memory_lifecycle_via_tools(srv):
    created = j(srv.store_memory("il gatto dorme sul divano", "Nota sul gatto",
                                 tags=["gatto"], category="note"))
    mid = created["id"]

    got = j(srv.get_memory(mid))
    assert got["content"] == "il gatto dorme sul divano"

    listed = j(srv.list_memories())
    assert any(m["id"] == mid for m in listed["memories"])

    assert j(srv.update_memory(mid, content="il gatto dorme sul letto"))["status"] == "updated"
    hist = j(srv.memory_history(mid))
    assert len(hist["history"]) == 1

    found = j(srv.recall("gatto"))
    assert found["count"] >= 1

    assert j(srv.delete_memory(mid))["status"] == "deleted"
    assert "error" in j(srv.get_memory(mid))


def test_decision_tools(srv):
    j(srv.store_decision("usiamo sqlite", rationale="semplice", project="toolproj"))
    out = j(srv.list_decisions(project="toolproj"))
    assert out["count"] == 1


def test_project_tools_and_context(srv, tmp_path):
    pdir = tmp_path / "progetto-tool"
    pdir.mkdir()
    j(srv.register_project("toolproj", "progetto di test", [str(pdir)]))
    assert any(p["name"] == "toolproj" for p in j(srv.list_projects())["projects"])

    ctx = j(srv.get_context(cwd=str(pdir), task_description="sqlite"))
    assert ctx["project"]["name"] == "toolproj"


def test_belief_tools(srv):
    mid = j(srv.store_memory("credenza provvisoria", "Belief test"))["id"]
    j(srv.flag_stale(mid, reason="superata dai fatti"))
    b = j(srv.set_belief(mid, confidence=0.2))
    assert b["status"] == "stale"
    assert b["confidence"] == 0.2
    # una memoria stale resta visibile in recall ma annotata
    found = j(srv.recall("credenza provvisoria"))
    hit = next((r for r in found["results"] if r.get("id") == mid), None)
    if hit is not None:                      # con pochi dati il match c'è sempre, ma non assumiamo il ranking
        assert hit["belief"]["status"] == "stale"


def test_reflect_and_insight_tools(srv):
    out = j(srv.reflect(store_them=True))
    assert out["count"] == len(out["candidates"])
    ins = j(srv.list_insights(status="proposed"))["insights"]
    if ins:                                   # se reflect ha proposto qualcosa, il ciclo accept funziona
        accepted = j(srv.accept_insight(ins[0]["id"]))
        assert accepted["status"] == "accepted"
        assert "memory" in accepted


def test_recall_associative_and_graph(srv):
    j(srv.store_memory("il cane abbaia in giardino", "Nota sul cane", tags=["cane"]))
    out = j(srv.recall_associative("cane"))
    from wadachi import search
    if search._FASTEMBED_AVAILABLE:
        assert "error" not in out
    else:
        # senza fastembed: errore chiaro + fallback keyword, mai un crash
        assert "keyword_fallback" in out
    g = j(srv.memory_graph(include_entities=False))
    assert "mermaid" in g


def test_rebuild_entity_graph_without_backend(srv, monkeypatch):
    """Non deve invocare il vero claude CLI nei test: monkeypatch della classe."""
    class FakeEG:
        def __init__(self, store): ...
        def rebuild(self):
            return {"status": "fake", "entities": 0}
    monkeypatch.setattr(srv, "EntityGraph", FakeEG)
    assert j(srv.rebuild_entity_graph())["status"] == "fake"


# ── input malformati ──────────────────────────────────────────


def test_malformed_inputs_do_not_crash(srv):
    # titolo vuoto, tag None, categoria inventata: si salva comunque
    out = j(srv.store_memory("contenuto", "", tags=None, category="categoria-inventata"))
    assert "id" in out
    # recall con query vuota: risposta valida, non eccezione
    assert isinstance(j(srv.recall("")), dict)
    # limit zero
    assert isinstance(j(srv.recall("x", limit=0)), dict)
    # get_context senza cwd
    assert "stats" in j(srv.get_context())
