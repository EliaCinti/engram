"""
beliefs.py — belief revision: tell the user when a memory has gone stale.

A plain store treats every memory as equally true forever. The brain shouldn't:
a workflow note from May that a June note explicitly overrode is *not* current,
and a "resets 1 Jul 00:00 UTC" note is dead weight after that date.

`BeliefReviewer.scan()` is a read-only pass that flags memories needing review,
fusing cheap signals (no LLM):

  1. supersession — a memory that another memory says it "updates" (typed edge
     from the citation graph) → likely stale, superseded_by the newer one.
  2. temporal     — a past date sitting next to a time cue (reset / deadline / UTC).
  3. conditional  — provisional / drift / fallback / TODO wording → re-validate.
  4. stored       — beliefs already marked stale/retired, or with valid_until elapsed.

It never deletes or rewrites: it annotates and suggests. The human (or a later
LLM pass) confirms via `set_belief` / `flag_stale`.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from engram.graph import MemoryGraph

_MONTHS = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6,
           "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*\.?(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
_TEMPORAL_CUE = ("reset", "utc", "deadline", "scade", "scadut", "fino al",
                 "entro il", "valid_until", "00:00")
# Tight, high-precision markers of a *provisional* belief (one whose truth
# depends on a condition that may have flipped). Kept deliberately narrow:
# broad words like "todo"/"per ora"/"finché" over-fired on ~40% of the brain.
_COND_CUE = ("drift", "workaround", "provvisor", "soluzione temporane",
             "in via temporane", "fallback", "quando gemini torna",
             "quando torna online", "finché gemini")

_PRIO = {"superseded": 0, "retired": 1, "expired": 2, "stale": 3,
         "temporal": 4, "conditional": 5}


def _today() -> date:
    return datetime.now(timezone.utc).date()


class BeliefReviewer:
    def __init__(self, store):
        self.store = store

    def scan(self, project: str | None = None, limit: int = 50) -> list[dict]:
        g = MemoryGraph(self.store).build(project)
        today = _today()
        stored = self.store.get_beliefs(project)
        flags: dict[int, dict] = {}

        def add(mid: int, signal: str, reason: str, superseded_by: int | None = None) -> None:
            if mid not in g.nodes:
                return
            f = flags.setdefault(mid, {"signals": set(), "reasons": [], "superseded_by": None})
            f["signals"].add(signal)
            f["reasons"].append(reason)
            if superseded_by:
                f["superseded_by"] = superseded_by

        # 1) supersession via typed 'updates' citation edges (newer -> older)
        for e in g.edges:
            if e.kind == "citation" and e.rel == "updates":
                add(e.dst, "superseded",
                    f"un'altra memoria (#{e.src}: {g.nodes[e.src].title[:40]}) dichiara di aggiornarla",
                    superseded_by=e.src)

        # 2) temporal + 3) conditional, from content
        for mid, node in g.nodes.items():
            low = node.content.lower()
            if any(c in low for c in _TEMPORAL_CUE):
                for m in _DATE_RE.finditer(node.content):
                    mon = _MONTHS.get(m.group(2).lower()[:3])
                    if not mon:
                        continue
                    yr = int(m.group(3)) if m.group(3) else today.year
                    try:
                        dt = date(yr, mon, int(m.group(1)))
                    except ValueError:
                        continue
                    if dt < today:
                        add(mid, "temporal", f"data passata ({dt.isoformat()}) accanto a un riferimento temporale")
                        break
            if any(c in low for c in _COND_CUE):
                add(mid, "conditional", "credenza condizionale/provvisoria: rivalidare se la condizione è cambiata")

        # 4) stored beliefs already flagged / expired
        for mid, b in stored.items():
            if b["status"] in ("stale", "retired"):
                add(mid, b["status"], b.get("review_reason") or f"stato '{b['status']}' impostato manualmente")
            vu = b.get("valid_until")
            if vu:
                try:
                    if date.fromisoformat(vu[:10]) < today:
                        add(mid, "expired", f"valid_until {vu} è passato")
                except ValueError:
                    pass

        out = []
        for mid, f in flags.items():
            sigs = sorted(f["signals"], key=lambda s: _PRIO.get(s, 9))
            out.append({
                "memory_id": mid,
                "title": g.nodes[mid].title,
                "signals": sigs,
                "reason": "; ".join(f["reasons"][:3]),
                "superseded_by": f["superseded_by"],
                "current_status": stored.get(mid, {}).get("status", "active"),
                "suggested_action": "flag_stale" if sigs[0] in ("superseded", "expired") else "review",
            })
        out.sort(key=lambda x: _PRIO.get(x["signals"][0], 9))
        return out[:limit]
