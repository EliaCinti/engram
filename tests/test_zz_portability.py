"""wadachi export/restore — la rete di sicurezza: read-only, portabile, roundtrip."""

import json
import sqlite3
import tarfile

import pytest

from wadachi.portability import export_brain, restore_brain


def _hash_tree(root):
    import hashlib
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def test_export_creates_archive_with_manifest(store, tmp_path):
    store.store_memory("contenuto prezioso", "Da Esportare", project="expproj")
    store.store_decision("scelta importante")

    res = export_brain(store.brain_dir, out=tmp_path / "out.tar.gz")
    m = res["manifest"]
    assert m["memories"] == 1 and m["decisions"] == 1
    assert m["markdown_files"] == 1
    assert m["schema_version"] >= 2

    with tarfile.open(res["archive"]) as tar:
        names = tar.getnames()
    assert "MANIFEST.json" in names
    assert "brain.db" in names
    assert any(n.startswith("projects/expproj/") for n in names)


def test_export_is_strictly_read_only(store, tmp_path):
    store.store_memory("x", "Intoccabile")
    before = _hash_tree(store.brain_dir)
    export_brain(store.brain_dir, out=tmp_path / "ro.tar.gz")
    assert _hash_tree(store.brain_dir) == before      # byte-identico


def test_export_legacy_engram_brain_untouched(tmp_path):
    """Il caso che conta: brain dell'era Engram, PRIMA di qualsiasi migrazione."""
    brain = tmp_path / "old-engram"
    (brain / "global").mkdir(parents=True)
    (brain / "global" / "ricordo.md").write_text("---\ntitle: R\n---\n\nprezioso")
    conn = sqlite3.connect(brain / "brain.db")       # schema vecchio, NO schema_version
    conn.execute("CREATE TABLE memories (id INTEGER PRIMARY KEY, title TEXT, slug TEXT, "
                 "project TEXT, tags TEXT, category TEXT, filepath TEXT, "
                 "created_at TEXT, updated_at TEXT, embedding BLOB)")
    conn.execute("INSERT INTO memories (title, slug, filepath, created_at, updated_at) "
                 "VALUES ('R', 'r', 'global/ricordo.md', '2026-01-01', '2026-01-01')")
    conn.commit(); conn.close()
    before = _hash_tree(brain)

    res = export_brain(brain, out=tmp_path / "legacy.tar.gz")

    assert res["manifest"]["schema_version"] == 0     # riconosciuto come pre-wadachi
    assert res["manifest"]["memories"] == 1
    assert _hash_tree(brain) == before                # nessuna migrazione partita
    assert not (brain / "backups").exists()


def test_restore_roundtrip(store, tmp_path):
    m = store.store_memory("andata e ritorno", "Roundtrip")
    res = export_brain(store.brain_dir, out=tmp_path / "rt.tar.gz")

    dest = tmp_path / "ripristinato"
    out = restore_brain(res["archive"], to=dest)
    assert json.loads((dest / "MANIFEST.json").read_text())["memories"] == 1

    # il brain ripristinato è usabile: lo apre un MemoryStore normale
    from wadachi.store import MemoryStore
    s2 = MemoryStore(str(dest))
    assert s2.get_memory(m["id"])["content"] == "andata e ritorno"


def test_restore_refuses_non_empty_without_force(store, tmp_path):
    res = export_brain(store.brain_dir, out=tmp_path / "a.tar.gz")
    dest = tmp_path / "occupata"
    dest.mkdir()
    (dest / "roba.txt").write_text("già qui")
    with pytest.raises(FileExistsError):
        restore_brain(res["archive"], to=dest)
    restore_brain(res["archive"], to=dest, force=True)   # con force passa
    assert (dest / "brain.db").exists()


def test_export_missing_brain_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_brain(tmp_path / "non-esiste")
