"""2.7 — `wadachi init`: setup guidato, idempotente, senza toccare Claude/Antigravity reali."""

import argparse
import json
import sqlite3

from wadachi.cli import cmd_init


def _args(**kw):
    base = dict(brain_dir=None, no_claude=True, no_antigravity=True, antigravity_dir=None)
    base.update(kw)
    return argparse.Namespace(**base)


def test_init_creates_brain_and_migrated_db(tmp_path, capsys):
    brain = tmp_path / "mio-brain"
    assert cmd_init(_args(brain_dir=str(brain))) == 0

    assert (brain / "global").is_dir()
    assert (brain / "projects").is_dir()
    conn = sqlite3.connect(brain / "brain.db")
    assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] >= 1
    conn.close()
    out = capsys.readouterr().out
    assert "migrazioni applicate" in out


def test_init_is_idempotent(tmp_path, capsys):
    brain = tmp_path / "b"
    assert cmd_init(_args(brain_dir=str(brain))) == 0
    assert cmd_init(_args(brain_dir=str(brain))) == 0     # seconda volta: nessun errore
    out = capsys.readouterr().out
    assert "già all'ultima versione" in out


def test_init_adopts_legacy_db_with_backup(tmp_path):
    """Upgrade da versione vecchia: memorie preservate + backup automatico."""
    brain = tmp_path / "legacy"
    brain.mkdir()
    conn = sqlite3.connect(brain / "brain.db")
    conn.executescript("""
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, slug TEXT NOT NULL,
            project TEXT NOT NULL DEFAULT 'global', tags TEXT DEFAULT '[]',
            category TEXT DEFAULT 'note', filepath TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, embedding BLOB
        );
        INSERT INTO memories (title, slug, filepath, created_at, updated_at)
        VALUES ('memoria preziosa', 'memoria-preziosa', 'global/x.md', '2026-01-01', '2026-01-01');
    """)
    conn.commit()
    conn.close()

    assert cmd_init(_args(brain_dir=str(brain))) == 0

    conn = sqlite3.connect(brain / "brain.db")
    assert conn.execute("SELECT title FROM memories").fetchone()[0] == "memoria preziosa"
    conn.close()
    assert list((brain / "backups").glob("brain.db.bak.*"))


def test_init_writes_antigravity_config(tmp_path):
    brain = tmp_path / "b"
    ag = tmp_path / "antigravity-ide"
    ag.mkdir()
    # config esistente con un altro server: viene preservato
    (ag / "mcp_config.json").write_text(json.dumps({"mcpServers": {"altro": {"command": "x"}}}))

    assert cmd_init(_args(brain_dir=str(brain), no_antigravity=False,
                          antigravity_dir=str(ag))) == 0

    cfg = json.loads((ag / "mcp_config.json").read_text())
    assert "altro" in cfg["mcpServers"]                    # non clobberato
    assert cfg["mcpServers"]["wadachi"]["env"]["BRAIN_DIR"] == str(brain)


def test_init_does_not_clobber_invalid_antigravity_json(tmp_path):
    brain = tmp_path / "b"
    ag = tmp_path / "antigravity-ide"
    ag.mkdir()
    (ag / "mcp_config.json").write_text("{json rotto")

    assert cmd_init(_args(brain_dir=str(brain), no_antigravity=False,
                          antigravity_dir=str(ag))) == 0
    assert (ag / "mcp_config.json").read_text() == "{json rotto"   # intatto


def test_cli_version(capsys):
    import pytest
    from wadachi.cli import main
    import sys
    argv = sys.argv
    sys.argv = ["wadachi", "--version"]
    try:
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
    finally:
        sys.argv = argv
    assert "wadachi" in capsys.readouterr().out
