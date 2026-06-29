"""
Constellation — associative memory graph + spreading-activation recall.

Engram already stores memories that CITE each other in prose ("memoria #82",
"aggiorna #77"). That latent citation graph is currently ignored: `recall` is
pure cosine top-k, so a memory that is strongly *connected* to your query — but
not textually similar to it — never surfaces.

This module surfaces and exploits that graph. It builds a weighted graph over
memories from two edge sources:

  1. CITATION edges (explicit, high precision): references like "memoria #N"
     parsed from the markdown body, typed as updates / contradicts / cites / relates.
  2. SEMANTIC edges (implicit): a k-NN graph over the cached bge-small embeddings.

Recall then runs Personalized PageRank (HippoRAG-style spreading activation):
the query's top semantic hits become "seeds", activation spreads along the
graph, and memories that sit in the seeds' neighbourhood get pulled up even when
their raw cosine score is low. The final ranking blends direct similarity with
graph proximity.

Design constraints:
  * ADDITIVE and READ-ONLY on the live brain. It does not write to brain.db and
    does not touch store.py / search.py / server.py.
  * Pure numpy. No new dependencies (numpy + fastembed are already required).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from engram.search import embed_text, embed_texts, cosine_similarity

# Reference like "memoria #82", "memorie 77", "memory #5" → memory id.
# Deliberately word-anchored (requires "memor..."): high precision, avoids
# matching bare "#1" that appears inside quoted external text.
_MEM_REF = re.compile(r"(?i)\bmemor(?:i[ae]|y|ies)\b[^\w#]{0,12}#?\s*(\d{1,4})")

_EDGE_WEIGHT = {"updates": 1.5, "contradicts": 1.2, "cites": 1.0, "relates": 0.8}

_UPDATE_KW = ("aggiorn", "update", "supersed", "sostitu", "rivede", "supera",
              "deprecat", "risolt", "rivalut")
_CONTRA_KW = ("contraddi", "contradic", "smentisc", "invalidan", "rettific")
_CITE_KW = ("vedi", "cfr", "cf.", "come da", "see ", "vedi ")


def _edge_type(window: str) -> str:
    w = window.lower()
    if any(k in w for k in _UPDATE_KW):
        return "updates"
    if any(k in w for k in _CONTRA_KW):
        return "contradicts"
    if any(k in w for k in _CITE_KW):
        return "cites"
    return "relates"


@dataclass
class Node:
    id: int
    title: str
    category: str
    tags: list[str]
    content: str
    emb: np.ndarray | None = None


@dataclass
class Edge:
    src: int          # memory id
    dst: int          # memory id
    kind: str         # citation | semantic
    rel: str          # updates / contradicts / cites / relates / similar
    weight: float


@dataclass
class MemoryGraph:
    store: object
    knn: int = 6
    sem_threshold: float = 0.62
    nodes: dict[int, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _order: list[int] = field(default_factory=list)        # stable id order
    _idx: dict[int, int] = field(default_factory=dict)     # id -> matrix index
    _W: np.ndarray | None = None

    # ── Build ────────────────────────────────────────────────────────────────

    def build(self, project: str | None = None) -> "MemoryGraph":
        rows = self.store.get_memories_for_embedding(project)
        # Materialise nodes + embeddings (compute missing ones IN MEMORY, no persist)
        missing_text, missing_ids = [], []
        for r in rows:
            emb = None
            if r["embedding"] is not None:
                emb = np.frombuffer(r["embedding"], dtype=np.float32)
            node = Node(r["id"], r["title"], r["category"], r["tags"], r["content"], emb)
            self.nodes[r["id"]] = node
            if emb is None:
                missing_ids.append(r["id"])
                missing_text.append(
                    f"{r['title']}. Tags: {', '.join(r['tags'])}. {r['content'][:1000]}"
                )
        if missing_text:
            embs = embed_texts(missing_text)
            if embs:
                for mid, e in zip(missing_ids, embs):
                    self.nodes[mid].emb = e

        self._order = sorted(self.nodes)
        self._idx = {mid: i for i, mid in enumerate(self._order)}

        self._build_citation_edges()
        self._build_semantic_edges()
        self._build_matrix()
        return self

    def _build_citation_edges(self) -> None:
        ids = set(self.nodes)
        for src, node in self.nodes.items():
            for m in _MEM_REF.finditer(node.content):
                dst = int(m.group(1))
                if dst == src or dst not in ids:
                    continue
                rel = _edge_type(node.content[max(0, m.start() - 40):m.start()])
                self.edges.append(Edge(src, dst, "citation", rel, _EDGE_WEIGHT[rel]))

    def _build_semantic_edges(self) -> None:
        ids = [mid for mid in self._order if self.nodes[mid].emb is not None]
        if len(ids) < 2:
            return
        M = np.vstack([self.nodes[mid].emb for mid in ids])
        M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
        sims = M @ M.T
        np.fill_diagonal(sims, -1.0)
        for a, mid in enumerate(ids):
            order = np.argsort(-sims[a])[: self.knn]
            for b in order:
                s = float(sims[a, b])
                if s < self.sem_threshold:
                    break
                i, j = mid, ids[b]
                if i < j:  # dedupe undirected
                    self.edges.append(Edge(i, j, "semantic", "similar", s))

    def _build_matrix(self) -> None:
        n = len(self._order)
        W = np.zeros((n, n), dtype=float)
        for e in self.edges:
            i, j = self._idx[e.src], self._idx[e.dst]
            if e.kind == "citation":
                W[i, j] += e.weight          # directed: citer -> cited
                W[j, i] += 0.5 * e.weight    # weaker reverse (related both ways)
            else:                            # semantic / entity: symmetric
                W[i, j] += e.weight
                W[j, i] += e.weight
        self._W = W

    # ── Bridge: ingest Graphify's entity graph ───────────────────────────────

    def load_entity_edges(self, graphify_json: str, weight: float = 0.9) -> int:
        """Enrich the memory graph with Graphify's extracted entities.

        Graphify (run for free via the local `claude` CLI) turns the brain's
        markdown into an entity knowledge graph. Two memories that both touch the
        same entity (e.g. both reference `convert.py`) get linked here — which
        connects memories that have no explicit citation and aren't textually
        similar. Mapping is by Graphify's `source_file`, matched to each memory's
        stored filepath (flattened: '/' -> '__'). Returns the number of edges added.
        """
        import json as _json
        from collections import defaultdict

        g = _json.load(open(graphify_json, encoding="utf-8"))
        gnodes = {n["id"]: n for n in g["nodes"]}
        adj: dict = defaultdict(set)
        for e in g.get("links", []):
            adj[e["source"]].add(e["target"])
            adj[e["target"]].add(e["source"])

        with self.store._conn() as conn:
            rows = conn.execute("SELECT id, filepath FROM memories").fetchall()
        flat_to_id = {r["filepath"].replace("/", "__"): r["id"] for r in rows}

        def mem_id(gnode: dict) -> int | None:
            return flat_to_id.get(gnode.get("source_file") or "")

        added = 0
        for nid, node in gnodes.items():
            if node.get("file_type") == "document":
                continue  # entities only (concept/code/paper/...)
            mems = sorted({mid for d in adj[nid]
                           if (mid := mem_id(gnodes[d])) is not None and mid in self.nodes})
            label = (node.get("label") or "entity")[:30]
            for a in range(len(mems)):
                for b in range(a + 1, len(mems)):
                    self.edges.append(Edge(mems[a], mems[b], "entity", f"shares:{label}", weight))
                    added += 1
        if added:
            self._build_matrix()
        return added

    # ── Personalized PageRank (spreading activation) ─────────────────────────

    def _ppr(self, personalization: np.ndarray, damping: float = 0.85,
             iters: int = 60, tol: float = 1e-7) -> np.ndarray:
        n = len(self._order)
        W = self._W
        cs = W.sum(axis=0)
        M = np.zeros_like(W)
        nz = cs > 0
        M[:, nz] = W[:, nz] / cs[nz]
        M[:, ~nz] = 1.0 / n                  # dangling nodes -> uniform
        p = personalization / (personalization.sum() + 1e-12)
        r = p.copy()
        for _ in range(iters):
            r_new = (1 - damping) * p + damping * (M @ r)
            if np.abs(r_new - r).sum() < tol:
                r = r_new
                break
            r = r_new
        return r

    # ── Associative recall ───────────────────────────────────────────────────

    def associative_recall(self, query: str, limit: int = 5, seeds: int = 5,
                           alpha: float = 0.5) -> dict:
        """Spreading-activation recall.

        alpha blends direct query similarity (alpha) with graph proximity (1-alpha).
        Returns both the associative ranking and the plain-cosine baseline, so the
        difference is auditable.
        """
        q = embed_text(query)
        if q is None:
            raise RuntimeError("No embedding model available (install fastembed).")
        order = self._order
        n = len(order)
        embs = np.vstack([
            (self.nodes[mid].emb if self.nodes[mid].emb is not None else np.zeros_like(q))
            for mid in order
        ])
        qsim = np.array([cosine_similarity(q, embs[i]) for i in range(n)])

        seed_idx = np.argsort(-qsim)[:seeds]
        p = np.zeros(n)
        p[seed_idx] = np.clip(qsim[seed_idx], 0, None)
        ppr = self._ppr(p)

        qn = self._norm(qsim)
        gn = self._norm(ppr)
        final = alpha * qn + (1 - alpha) * gn

        baseline_ids = [order[i] for i in np.argsort(-qsim)[:limit]]
        ranked = np.argsort(-final)
        results = []
        for i in ranked[:limit]:
            mid = order[i]
            results.append({
                "id": mid,
                "title": self.nodes[mid].title,
                "final": round(float(final[i]), 3),
                "direct_sim": round(float(qsim[i]), 3),
                "graph_score": round(float(gn[i]), 3),
                "via": self._activators(mid, seed_idx),
                "new_vs_cosine": mid not in baseline_ids,
            })
        return {
            "query": query,
            "associative": results,
            "baseline_cosine": baseline_ids,
            "seeds": [order[i] for i in seed_idx],
        }

    def _activators(self, mid: int, seed_idx: np.ndarray) -> list[int]:
        """Which seed memories have an edge to `mid` (explains the activation)."""
        seeds = {self._order[i] for i in seed_idx}
        out = set()
        for e in self.edges:
            if e.src == mid and e.dst in seeds:
                out.add(e.dst)
            if e.dst == mid and e.src in seeds:
                out.add(e.src)
        return sorted(out)

    @staticmethod
    def _norm(v: np.ndarray) -> np.ndarray:
        lo, hi = float(v.min()), float(v.max())
        return (v - lo) / (hi - lo) if hi > lo else np.zeros_like(v)

    # ── Introspection ────────────────────────────────────────────────────────

    def related(self, memory_id: int, limit: int = 8) -> list[dict]:
        out = []
        for e in self.edges:
            other = None
            if e.src == memory_id:
                other = e.dst
            elif e.dst == memory_id:
                other = e.src
            if other is not None:
                out.append({"id": other, "title": self.nodes[other].title,
                            "kind": e.kind, "rel": e.rel, "weight": round(e.weight, 3)})
        out.sort(key=lambda x: x["weight"], reverse=True)
        return out[:limit]

    def stats(self) -> dict:
        cit = [e for e in self.edges if e.kind == "citation"]
        sem = [e for e in self.edges if e.kind == "semantic"]
        deg: dict[int, int] = {mid: 0 for mid in self.nodes}
        for e in self.edges:
            deg[e.src] += 1
            deg[e.dst] += 1
        rel_counts: dict[str, int] = {}
        for e in cit:
            rel_counts[e.rel] = rel_counts.get(e.rel, 0) + 1
        hubs = sorted(deg.items(), key=lambda kv: kv[1], reverse=True)[:5]
        orphans = [mid for mid, d in deg.items() if d == 0]
        return {
            "nodes": len(self.nodes),
            "citation_edges": len(cit),
            "citation_by_rel": rel_counts,
            "semantic_edges": len(sem),
            "hubs": [{"id": mid, "degree": d, "title": self.nodes[mid].title} for mid, d in hubs],
            "orphans": orphans,
        }

    def to_mermaid(self, focus: int | None = None, max_nodes: int = 30) -> str:
        """Mermaid `graph` of the citation backbone (optionally around one node)."""
        cit = [e for e in self.edges if e.kind == "citation"]
        if focus is not None:
            keep = {focus} | {e.dst for e in cit if e.src == focus} | {e.src for e in cit if e.dst == focus}
            cit = [e for e in cit if e.src in keep and e.dst in keep]
        shown, lines = set(), ["graph LR"]
        arrow = {"updates": "-->|updates|", "contradicts": "-.->|contradicts|",
                 "cites": "-->|cites|", "relates": "-->"}
        for e in cit[:max_nodes * 2]:
            for mid in (e.src, e.dst):
                if mid not in shown:
                    label = self.nodes[mid].title[:34].replace('"', "'")
                    lines.append(f'  m{mid}["#{mid} {label}"]')
                    shown.add(mid)
            lines.append(f"  m{e.src} {arrow.get(e.rel, '-->')} m{e.dst}")
        return "\n".join(lines)
