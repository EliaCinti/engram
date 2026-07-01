"""
procedural.py — learn to act (Phase 3, procedural pillar).

A passive memory only fires if recalled at the right moment — and the brain has a
documented case where recency-ranked recall *hid* the right rule, causing the same
mistake twice. Procedural memory compiles recurring lessons *out of* the recall
lottery: it finds clusters of incident memories that share a root theme and proposes
a single always-on rule for review.

Read-only and human-in-the-loop: it surfaces candidate rules with their source
incidents and recurrence count. It NEVER edits the operating instructions itself.
"""

from __future__ import annotations

from collections import defaultdict

# Tags/words that mark a memory as an "incident / lesson learned".
_INCIDENT_TAGS = {"anti-drift", "drift", "bug-ricorrente", "duplicato", "anti-duplicato",
                  "incident", "bugfix", "ricorrente", "fix", "anti-pattern", "rollback"}
_INCIDENT_WORDS = ("bug", "drift", "duplicat", "ricorrente", "anti-", "overwrite", "sovrascr")
# Tags that name a topic/area/project, not a recurring *failure theme* — they'd
# cluster unrelated incidents that merely share a subject, so exclude them.
_GENERIC = {"fix", "bugfix", "config", "pipeline", "workflow", "latex", "katex",
            "feynotes", "cem", "studycoach", "geometria-solver", "engram",
            "fisica1", "geometria", "algebra", "fdc", "gip"}


class ProceduralReviewer:
    def __init__(self, store):
        self.store = store

    def review(self, project: str | None = None, min_cluster: int = 2) -> list[dict]:
        mems = self.store.list_memories(project=project)
        incidents = []
        for m in mems:
            tags = {t.lower() for t in m["tags"]}
            title = m["title"].lower()
            if (m["category"] == "bugfix" or (tags & _INCIDENT_TAGS)
                    or any(w in title for w in _INCIDENT_WORDS)):
                incidents.append({"id": m["id"], "title": m["title"], "tags": tags})

        by_tag: dict = defaultdict(list)
        for m in incidents:
            for t in m["tags"]:
                if t not in _GENERIC:
                    by_tag[t].append(m["id"])

        rules, seen = [], set()
        for theme, ids in by_tag.items():
            if len(ids) < min_cluster:
                continue
            key = frozenset(ids)
            if key in seen:
                continue
            seen.add(key)
            titles = [next(i["title"] for i in incidents if i["id"] == mid)[:44] for mid in ids]
            rules.append({
                "theme": theme,
                "recurrence": len(ids),
                "source_ids": sorted(ids),
                "candidate_rule": (f"Tema ricorrente «{theme}» in {len(ids)} memorie-incidente "
                                   f"({sorted(ids)}) → valuta una regola always-on nell'istruzione operativa."),
                "sources": titles,
            })
        rules.sort(key=lambda r: r["recurrence"], reverse=True)
        return rules
