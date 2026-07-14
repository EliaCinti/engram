"""3.9 — Parser Markdown tollerante: mai eccezioni, sempre (meta, content)."""

from wadachi.mdio import parse_memory_file, render_memory_file, backfill_file


def test_canonical_roundtrip():
    meta = {"title": "T", "project": "p", "tags": ["a", "b"], "category": "note",
            "created": "2026-01-01"}
    text = render_memory_file(meta, "il contenuto")
    p = parse_memory_file(text)
    assert p.had_frontmatter and not p.malformed
    assert p.meta["title"] == "T"
    assert p.meta["tags"] == ["a", "b"]
    assert p.content == "il contenuto"


def test_no_frontmatter_is_all_content():
    p = parse_memory_file("solo testo, scritto a mano\nsu due righe")
    assert not p.had_frontmatter and not p.malformed
    assert p.content.startswith("solo testo")


def test_unclosed_frontmatter():
    p = parse_memory_file("---\ntitle: X\ncategory: note\n\nil corpo senza chiusura")
    assert p.malformed
    assert p.meta.get("title") == "X"
    assert "corpo senza chiusura" in p.content


def test_garbage_line_in_frontmatter():
    p = parse_memory_file("---\ntitle: X\nquesta riga non è chiave-valore!\n---\n\ncorpo")
    assert p.malformed
    assert p.meta["title"] == "X"
    assert p.content == "corpo"


def test_tags_formats():
    for raw, expected in [
        ('["a", "b"]', ["a", "b"]),          # JSON
        ("[a, b]", ["a", "b"]),              # YAML inline
        ("a, b", ["a", "b"]),                # CSV
        ("", []),
    ]:
        p = parse_memory_file(f"---\ntags: {raw}\n---\n\nx")
        assert p.meta["tags"] == expected, raw


def test_content_with_horizontal_rules():
    """Un --- nel corpo non confonde il parser."""
    text = "---\ntitle: X\n---\n\nprima parte\n\n---\n\nseconda parte"
    p = parse_memory_file(text)
    assert "prima parte" in p.content and "seconda parte" in p.content


def test_empty_and_binaryish_input():
    assert parse_memory_file("").content == ""
    assert parse_memory_file("\x00\x01\x02").content  # non alza eccezioni


def test_backfill_rewrites_only_when_needed(tmp_path):
    db_meta = {"title": "T", "project": "global", "tags": [], "category": "note",
               "created": "2026-01-01"}
    f = tmp_path / "m.md"
    f.write_text("contenuto scritto a mano, senza frontmatter")
    assert backfill_file(f, db_meta) is True
    text = f.read_text()
    assert text.startswith("---\ntitle: T")
    assert "contenuto scritto a mano" in text
    # ora è canonico: secondo giro = nessuna riscrittura
    assert backfill_file(f, db_meta) is False
