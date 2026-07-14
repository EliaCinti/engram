"""7.A — LLM Wiki: frontmatter OKF, wikilink nel grafo, index.md/log.md, SCHEMA.md."""

import argparse

from wadachi.graph import MemoryGraph
from wadachi.mdio import parse_memory_file, render_memory_file


# ── OKF: type nel formato canonico ────────────────────────────


def test_render_includes_okf_type():
    text = render_memory_file({"title": "T"}, "x")
    assert text.startswith("---\ntype: memory\n")


def test_new_memories_are_okf_conformant(store):
    r = store.store_memory("contenuto", "Conforme", tags=["a"])
    text = (store.brain_dir / r["filepath"]).read_text()
    parsed = parse_memory_file(text)
    assert parsed.meta["type"] == "memory"      # unico campo OKF richiesto
    assert parsed.meta["title"] == "Conforme"


def test_update_keeps_okf_type(store):
    r = store.store_memory("v1", "Aggiornata")
    store.update_memory(r["id"], content="v2")
    parsed = parse_memory_file((store.brain_dir / r["filepath"]).read_text())
    assert parsed.meta["type"] == "memory"
    assert "updated" in parsed.meta


# ── wikilink → archi citation nel grafo ───────────────────────


def test_wikilink_slug_becomes_citation_edge(store):
    a = store.store_memory("la base di tutto", "Nota Base")
    b = store.store_memory("vedi [[nota-base]] per il contesto", "Nota Derivata")
    g = MemoryGraph(store).build()
    cites = [(e.src, e.dst) for e in g.edges if e.kind == "citation"]
    assert (b["id"], a["id"]) in cites


def test_wikilink_id_ref_becomes_edge(store):
    """Il formato [[#id]] scritto da merge_memories ora crea archi (gap chiuso)."""
    a = store.store_memory("originale", "Fonte")
    b = store.store_memory(f"Consolida: [[#{a['id']}]]", "Sintesi")
    g = MemoryGraph(store).build()
    cites = [(e.src, e.dst) for e in g.edges if e.kind == "citation"]
    assert (b["id"], a["id"]) in cites


def test_wikilink_alias_and_unknown(store):
    a = store.store_memory("x", "Target Vero")
    b = store.store_memory(
        "vedi [[target-vero|questa nota]] ma non [[pagina-che-non-esiste]]",
        "Con alias")
    g = MemoryGraph(store).build()
    cites = [(e.src, e.dst) for e in g.edges if e.kind == "citation"]
    assert (b["id"], a["id"]) in cites          # alias risolto
    assert len(cites) == 1                       # il link rotto non crea archi


def test_duplicate_refs_deduped(store):
    a = store.store_memory("x", "Unica")
    b = store.store_memory(f"[[unica]] e ancora [[#{a['id']}]] e memoria #{a['id']}",
                           "Ripetitiva")
    g = MemoryGraph(store).build()
    cites = [(e.src, e.dst, e.rel) for e in g.edges if e.kind == "citation"]
    assert len(cites) == len(set(cites))         # nessun arco duplicato


# ── index.md + log.md (nomi riservati OKF) ────────────────────


def test_index_md_maintained(store):
    r = store.store_memory("x", "Indicizzata", project="wikiproj")
    index = (store.brain_dir / "index.md").read_text()
    assert "## wikiproj" in index
    assert "[[indicizzata]]" in index
    store.delete_memory(r["id"])
    index = (store.brain_dir / "index.md").read_text()
    assert "[[indicizzata]]" not in index


def test_log_md_append_only(store):
    a = store.store_memory("x", "Loggata")
    store.delete_memory(a["id"])
    log = (store.brain_dir / "log.md").read_text()
    lines = [ln for ln in log.splitlines() if ln.startswith("## [")]
    assert len(lines) == 2                       # store + delete
    assert "store" in lines[0] and "delete" in lines[1]


# ── SCHEMA.md via init, conformità via doctor --fix ───────────


def test_init_writes_schema_md(tmp_path):
    from wadachi.cli import cmd_init
    args = argparse.Namespace(brain_dir=str(tmp_path / "b"), no_claude=True,
                              no_antigravity=True, antigravity_dir=None)
    assert cmd_init(args) == 0
    schema = (tmp_path / "b" / "SCHEMA.md").read_text()
    assert "type: schema" in schema and "wikilink" in schema.lower()
    assert (tmp_path / "b" / "index.md").exists()


def test_doctor_fix_upgrades_legacy_files_to_okf(store, capsys):
    from wadachi.doctor import run_doctor
    r = store.store_memory("contenuto storico", "Legacy")
    path = store.brain_dir / r["filepath"]
    # simula un file dell'era pre-OKF: frontmatter senza `type`
    path.write_text("---\ntitle: Legacy\ncategory: note\n---\n\ncontenuto storico")

    assert run_doctor(store.brain_dir, fix=True, check_mcp=False) == 0
    parsed = parse_memory_file(path.read_text())
    assert parsed.meta["type"] == "memory"       # ora OKF-conforme
    assert parsed.content == "contenuto storico"
