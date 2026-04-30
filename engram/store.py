"""
Memory Store — SQLite metadata + markdown files on disk.

Storage layout:
    ~/.brain/
    ├── config.json
    ├── brain.db              # SQLite: metadata, embeddings cache, decisions
    ├── global/               # Cross-project memories
    │   └── *.md
    └── projects/
        ├── feynotes/
        │   └── *.md
        └── laplacebo/
            └── *.md
"""

import sqlite3
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _slugify(text: str) -> str:
    """Turn a title into a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


class MemoryStore:
    def __init__(self, brain_dir: Optional[str] = None):
        self.brain_dir = Path(brain_dir or os.environ.get("BRAIN_DIR", os.path.expanduser("~/.engram")))
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        (self.brain_dir / "global").mkdir(exist_ok=True)
        (self.brain_dir / "projects").mkdir(exist_ok=True)

        self.db_path = self.brain_dir / "brain.db"
        self._init_db()

    # ── Database ──────────────────────────────────────────────

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT NOT NULL,
                    slug        TEXT NOT NULL,
                    project     TEXT NOT NULL DEFAULT 'global',
                    tags        TEXT DEFAULT '[]',
                    category    TEXT DEFAULT 'note',
                    filepath    TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    embedding   BLOB
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project     TEXT NOT NULL DEFAULT 'global',
                    decision    TEXT NOT NULL,
                    rationale   TEXT,
                    alternatives TEXT,
                    context     TEXT,
                    created_at  TEXT NOT NULL,
                    embedding   BLOB
                );

                CREATE TABLE IF NOT EXISTS projects (
                    name        TEXT PRIMARY KEY,
                    description TEXT,
                    paths       TEXT DEFAULT '[]',
                    created_at  TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project);
                CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project);
            """)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Memory CRUD ───────────────────────────────────────────

    def store_memory(
        self,
        content: str,
        title: str,
        project: str = "global",
        tags: list[str] | None = None,
        category: str = "note",
    ) -> dict:
        """Store a memory as markdown file + metadata row."""
        now = datetime.now(timezone.utc).isoformat()
        slug = _slugify(title)
        tags = tags or []

        # Ensure project directory exists
        proj_dir = self._project_dir(project)
        proj_dir.mkdir(parents=True, exist_ok=True)

        # Avoid name collisions
        filepath = proj_dir / f"{slug}.md"
        counter = 1
        while filepath.exists():
            filepath = proj_dir / f"{slug}-{counter}.md"
            counter += 1

        # Write markdown with frontmatter
        frontmatter = (
            f"---\n"
            f"title: {title}\n"
            f"project: {project}\n"
            f"tags: {json.dumps(tags)}\n"
            f"category: {category}\n"
            f"created: {now}\n"
            f"---\n\n"
        )
        filepath.write_text(frontmatter + content, encoding="utf-8")

        # Insert metadata
        rel_path = str(filepath.relative_to(self.brain_dir))
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO memories (title, slug, project, tags, category, filepath, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, slug, project, json.dumps(tags), category, rel_path, now, now),
            )
            memory_id = cursor.lastrowid

        return {
            "id": memory_id,
            "title": title,
            "project": project,
            "filepath": rel_path,
            "created_at": now,
        }

    def get_memory(self, memory_id: int) -> dict | None:
        """Retrieve a memory by ID, including file content."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            return None

        filepath = self.brain_dir / row["filepath"]
        content = filepath.read_text(encoding="utf-8") if filepath.exists() else "[file missing]"
        # Strip frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return {
            "id": row["id"],
            "title": row["title"],
            "project": row["project"],
            "tags": json.loads(row["tags"]),
            "category": row["category"],
            "content": content,
            "filepath": row["filepath"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_memories(self, project: str | None = None, category: str | None = None) -> list[dict]:
        """List memories, optionally filtered by project and/or category."""
        query = "SELECT id, title, project, tags, category, filepath, created_at FROM memories WHERE 1=1"
        params: list = []
        if project:
            query += " AND project = ?"
            params.append(project)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY updated_at DESC"

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "project": r["project"],
                "tags": json.loads(r["tags"]),
                "category": r["category"],
                "filepath": r["filepath"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory (db row + file)."""
        with self._conn() as conn:
            row = conn.execute("SELECT filepath FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return False
            filepath = self.brain_dir / row["filepath"]
            if filepath.exists():
                filepath.unlink()
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return True

    def update_memory(self, memory_id: int, content: str | None = None, tags: list[str] | None = None) -> bool:
        """Update a memory's content and/or tags."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return False

            now = datetime.now(timezone.utc).isoformat()

            if content is not None:
                filepath = self.brain_dir / row["filepath"]
                frontmatter = (
                    f"---\n"
                    f"title: {row['title']}\n"
                    f"project: {row['project']}\n"
                    f"tags: {json.dumps(tags or json.loads(row['tags']))}\n"
                    f"category: {row['category']}\n"
                    f"created: {row['created_at']}\n"
                    f"updated: {now}\n"
                    f"---\n\n"
                )
                filepath.write_text(frontmatter + content, encoding="utf-8")

            updates = ["updated_at = ?"]
            params: list = [now]
            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags))
            # Clear cached embedding so it gets recomputed
            updates.append("embedding = NULL")
            params.append(memory_id)

            conn.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)
        return True

    # ── Decisions ─────────────────────────────────────────────

    def store_decision(
        self,
        decision: str,
        rationale: str = "",
        alternatives: str = "",
        context: str = "",
        project: str = "global",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO decisions (project, decision, rationale, alternatives, context, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project, decision, rationale, alternatives, context, now),
            )
            return {
                "id": cursor.lastrowid,
                "decision": decision,
                "project": project,
                "created_at": now,
            }

    def list_decisions(self, project: str | None = None, limit: int = 20) -> list[dict]:
        query = "SELECT * FROM decisions"
        params: list = []
        if project:
            query += " WHERE project = ?"
            params.append(project)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": r["id"],
                "decision": r["decision"],
                "rationale": r["rationale"],
                "alternatives": r["alternatives"],
                "context": r["context"],
                "project": r["project"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ── Projects ──────────────────────────────────────────────

    def register_project(self, name: str, description: str = "", paths: list[str] | None = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        paths = paths or []
        (self.brain_dir / "projects" / name).mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO projects (name, description, paths, created_at)
                   VALUES (?, ?, ?, ?)""",
                (name, description, json.dumps(paths), now),
            )
        return {"name": name, "description": description, "paths": paths}

    def detect_project(self, cwd: str) -> str | None:
        """Detect project from current working directory."""
        cwd = os.path.realpath(cwd)
        with self._conn() as conn:
            rows = conn.execute("SELECT name, paths FROM projects").fetchall()
        for row in rows:
            for path in json.loads(row["paths"]):
                if cwd.startswith(os.path.realpath(path)):
                    return row["name"]
        return None

    def list_projects(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [
            {
                "name": r["name"],
                "description": r["description"],
                "paths": json.loads(r["paths"]),
            }
            for r in rows
        ]

    # ── Embedding helpers (used by search.py) ─────────────────

    def get_memories_for_embedding(self, project: str | None = None) -> list[dict]:
        """Get memories that need embedding or all memories for search."""
        query = "SELECT id, title, tags, category, filepath, embedding FROM memories WHERE 1=1"
        params: list = []
        if project:
            query += " AND (project = ? OR project = 'global')"
            params.append(project)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            filepath = self.brain_dir / r["filepath"]
            content = ""
            if filepath.exists():
                raw = filepath.read_text(encoding="utf-8")
                if raw.startswith("---"):
                    parts = raw.split("---", 2)
                    content = parts[2].strip() if len(parts) >= 3 else raw
                else:
                    content = raw

            results.append({
                "id": r["id"],
                "title": r["title"],
                "tags": json.loads(r["tags"]),
                "category": r["category"],
                "content": content,
                "has_embedding": r["embedding"] is not None,
                "embedding": r["embedding"],
            })
        return results

    def get_decisions_for_embedding(self, project: str | None = None) -> list[dict]:
        query = "SELECT id, decision, rationale, context, project, embedding FROM decisions WHERE 1=1"
        params: list = []
        if project:
            query += " AND (project = ? OR project = 'global')"
            params.append(project)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": r["id"],
                "decision": r["decision"],
                "rationale": r["rationale"] or "",
                "context": r["context"] or "",
                "project": r["project"],
                "has_embedding": r["embedding"] is not None,
                "embedding": r["embedding"],
            }
            for r in rows
        ]

    def save_embedding(self, table: str, row_id: int, embedding_bytes: bytes):
        with self._conn() as conn:
            conn.execute(f"UPDATE {table} SET embedding = ? WHERE id = ?", (embedding_bytes, row_id))

    # ── Helpers ────────────────────────────────────────────────

    def _project_dir(self, project: str) -> Path:
        if project == "global":
            return self.brain_dir / "global"
        return self.brain_dir / "projects" / project

    def stats(self) -> dict:
        with self._conn() as conn:
            mem_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            dec_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
            proj_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        return {"memories": mem_count, "decisions": dec_count, "projects": proj_count}
