"""wadachi obsidian — backfill wikilink SU RICHIESTA: prosa intatta, versionato, idempotente."""

from wadachi.obsidian import run_backfill, MARKER


def test_backfill_appends_links_section(store):
    a = store.store_memory("la base", "Nota Base Obsidian")
    b = store.store_memory(f"vedi memoria #{a['id']} e anche [[#{a['id']}]]", "Che Cita")

    st = run_backfill(store.brain_dir)
    assert st["updated"] == 1 and st["links"] == 1     # dedupe dei due riferimenti

    text = (store.brain_dir / b["filepath"]).read_text()
    assert MARKER in text
    assert "[[nota-base-obsidian]]" in text
    # la prosa è intatta e la memoria si rilegge normalmente
    assert f"vedi memoria #{a['id']}" in text
    got = store.get_memory(b["id"])
    assert got["content"].startswith("vedi memoria")


def test_backfill_is_idempotent(store):
    a = store.store_memory("x", "Target Idem")
    store.store_memory(f"cita [[#{a['id']}]]", "Fonte Idem")
    assert run_backfill(store.brain_dir)["updated"] == 1
    assert run_backfill(store.brain_dir)["updated"] == 0   # secondo giro: nulla da fare


def test_backfill_dry_run_touches_nothing(store):
    a = store.store_memory("x", "Target Dry")
    b = store.store_memory(f"cita memoria #{a['id']}", "Fonte Dry")
    before = (store.brain_dir / b["filepath"]).read_text()
    st = run_backfill(store.brain_dir, dry_run=True)
    assert st["updated"] == 1                              # riporta cosa farebbe
    assert (store.brain_dir / b["filepath"]).read_text() == before


def test_backfill_versions_and_invalidates_embedding(store):
    import sqlite3
    a = store.store_memory("x", "Target Ver")
    b = store.store_memory(f"cita memoria #{a['id']}", "Fonte Ver")
    conn = sqlite3.connect(store.db_path)
    conn.execute("UPDATE memories SET embedding = X'00' WHERE id = ?", (b["id"],))
    conn.commit(); conn.close()

    run_backfill(store.brain_dir)

    hist = store.get_memory_history(b["id"])
    assert len(hist) == 1                                  # versione pre-backfill conservata
    import sqlite3 as s3
    conn = s3.connect(store.db_path)
    emb = conn.execute("SELECT embedding FROM memories WHERE id = ?", (b["id"],)).fetchone()[0]
    conn.close()
    assert emb is None                                     # cache invalidata


def test_backfill_handles_unresolved_and_no_refs(store):
    store.store_memory("cita memoria #9999 che non esiste", "Fonte Rotta")
    store.store_memory("nessun riferimento qui", "Solitaria")
    st = run_backfill(store.brain_dir)
    assert st["unresolved"] == 1
    assert st["links"] == 0
