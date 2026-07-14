"""
mdio — lettura/scrittura tollerante dei file memoria Markdown.

I file .md sono la fonte di verità del contenuto e possono essere editati a
mano (è una feature): questo modulo li legge SENZA mai alzare eccezioni per
un frontmatter assente, malformato o non chiuso, e sa riscriverli nel formato
canonico corrente (backfill) usando i metadata del DB come riferimento.

Formato canonico (OKF-conforme: https://github.com/GoogleCloudPlatform/knowledge-catalog —
l'unico campo richiesto dalla spec è `type`; gli altri sono estensioni tollerate):
    ---
    type: memory
    title: <titolo>
    project: <progetto>
    tags: ["a", "b"]
    category: <categoria>
    created: <iso>
    [updated: <iso>]
    ---

    <contenuto con [[wikilink]] in stile Obsidian>
"""

import json
import re
from dataclasses import dataclass, field


@dataclass
class ParsedMemory:
    meta: dict = field(default_factory=dict)
    content: str = ""
    had_frontmatter: bool = False
    malformed: bool = False          # frontmatter presente ma rotto/non chiuso
    warnings: list = field(default_factory=list)


def _parse_tags(raw: str) -> list:
    """Tag come JSON (["a","b"]), YAML inline ([a, b]) o CSV (a, b)."""
    raw = raw.strip()
    if not raw:
        return []
    try:
        v = json.loads(raw)
        if isinstance(v, list):
            return [str(x) for x in v]
    except (json.JSONDecodeError, ValueError):
        pass
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]


def parse_memory_file(text: str) -> ParsedMemory:
    """Parser tollerante: qualunque input produce (meta, content), mai eccezioni."""
    p = ParsedMemory()
    if not text.lstrip().startswith("---"):
        # nessun frontmatter: tutto è contenuto
        p.content = text.strip()
        return p

    # trova la riga di apertura e quella di chiusura del frontmatter
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.strip().startswith("---"))
    end = None
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end is None:
        # frontmatter non chiuso: header trattato come meta finché sembra
        # `chiave: valore`, il resto come contenuto
        p.had_frontmatter = True
        p.malformed = True
        p.warnings.append("frontmatter non chiuso (manca il --- finale)")
        body_start = start + 1
        for i in range(start + 1, len(lines)):
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
            if not m:
                body_start = i
                break
            p.meta[m.group(1).lower()] = m.group(2).strip()
            body_start = i + 1
        p.content = "\n".join(lines[body_start:]).strip()
    else:
        p.had_frontmatter = True
        for ln in lines[start + 1:end]:
            if not ln.strip():
                continue
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", ln)
            if m:
                p.meta[m.group(1).lower()] = m.group(2).strip()
            else:
                p.malformed = True
                p.warnings.append(f"riga di frontmatter non riconosciuta: {ln.strip()[:60]!r}")
        p.content = "\n".join(lines[end + 1:]).strip()

    if "tags" in p.meta:
        p.meta["tags"] = _parse_tags(p.meta["tags"])
    return p


def render_memory_file(meta: dict, content: str) -> str:
    """Serializza nel formato canonico corrente (OKF: `type` sempre presente)."""
    meta = {"type": "memory", **meta}
    lines = ["---"]
    for key in ("type", "title", "project", "tags", "category", "created", "updated"):
        if key not in meta or meta[key] in (None, ""):
            continue
        value = meta[key]
        if key == "tags":
            value = json.dumps(list(value))
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + content


def backfill_file(path, db_meta: dict) -> bool:
    """Riscrive un file nel formato canonico usando i metadata del DB.

    Ritorna True se il file è stato riscritto, False se era già canonico.
    Il contenuto viene SEMPRE preservato (è la parte preziosa); i metadata
    del DB vincono su quelli del file (il DB è l'indice autorevole).
    """
    text = path.read_text(encoding="utf-8")
    parsed = parse_memory_file(text)

    canonical = render_memory_file(db_meta, parsed.content)
    if text == canonical:
        return False
    path.write_text(canonical, encoding="utf-8")
    return True
