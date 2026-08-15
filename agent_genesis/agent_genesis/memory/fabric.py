"""
Agent Genesis — Memory Fabric
Shared memory layer (episodic / semantic / procedural) for all agents
across all runtimes (Hermes, Claude Code, Codex, local LLMs, Box).

SQLite for structured data + optional numpy/faiss for embeddings.
Pure-stdlib mode works with zero deps (embedding via hash fallback).
"""

from __future__ import annotations

import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import numpy as np  # type: ignore  # noqa: F401  (optional availability check)

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

DEFAULT_BASE = Path.home() / "agent-genesis" / "memory"


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class MemoryFabric:
    """Episodic + semantic + procedural memory with cross-agent sharing."""

    def __init__(self, base_path: str | Path = DEFAULT_BASE):
        self.base = Path(base_path).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base / "memory.db"
        self.db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    # ------------------------------------------------------------------ schema
    def _init_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS episodic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task_id TEXT,
                event_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS semantic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                concept TEXT NOT NULL,
                fact TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'observation',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS procedural (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                skill_name TEXT NOT NULL,
                description TEXT,
                steps TEXT NOT NULL,
                preconditions TEXT DEFAULT '{}',
                postconditions TEXT DEFAULT '{}',
                success_rate REAL DEFAULT 0.0,
                execution_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orgs (
                id TEXT PRIMARY KEY,
                spec TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS runtime_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_episodic_agent ON episodic(agent_id);
            CREATE INDEX IF NOT EXISTS idx_episodic_task ON episodic(task_id);
            CREATE INDEX IF NOT EXISTS idx_semantic_concept ON semantic(concept);
            CREATE INDEX IF NOT EXISTS idx_procedural_skill ON procedural(skill_name);
            """
        )
        self.db.commit()

    # ------------------------------------------------------- runtime state
    def set_state(self, key: str, value: Dict) -> None:
        """Upsert a shared runtime-state key (e.g. deployer live load).

        SQLite-backed so separate processes (``genesis deploy`` vs
        ``genesis status --watch``) can share live state.
        """
        self.db.execute(
            """INSERT INTO runtime_state (key, value, updated_at) VALUES (?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP""",
            (key, json.dumps(value)),
        )
        self.db.commit()

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Read a runtime-state key; returns None when unset."""
        row = self.db.execute(
            "SELECT value FROM runtime_state WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return None

    # ------------------------------------------------------------- episodic
    def remember(
        self,
        agent_id: str,
        event_type: str,
        content: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> int:
        cur = self.db.execute(
            "INSERT INTO episodic (agent_id, task_id, event_type, content, metadata) VALUES (?,?,?,?,?)",
            (agent_id, task_id, event_type, content, json.dumps(metadata or {})),
        )
        self.db.commit()
        return int(cur.lastrowid)

    def recall(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        q = "SELECT * FROM episodic WHERE 1=1"
        params: List[Any] = []
        if agent_id:
            q += " AND agent_id = ?"
            params.append(agent_id)
        if task_id:
            q += " AND task_id = ?"
            params.append(task_id)
        if event_type:
            q += " AND event_type = ?"
            params.append(event_type)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def recent_failures(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Pull error/correction episodes from the last N hours (for fine-tune loop)."""
        rows = self.db.execute(
            """SELECT * FROM episodic
               WHERE event_type IN ('error','failure','correction','human_feedback')
                 AND datetime(created_at) > datetime('now', ?)
               ORDER BY id DESC LIMIT ?""",
            (f"-{hours} hours", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------- semantic
    def learn_fact(
        self,
        concept: str,
        fact: str,
        agent_id: Optional[str] = None,
        confidence: float = 1.0,
        source: str = "observation",
    ) -> int:
        cur = self.db.execute(
            """INSERT INTO semantic (agent_id, concept, fact, confidence, source)
               VALUES (?,?,?,?,?)""",
            (agent_id, concept, fact, confidence, source),
        )
        self.db.commit()
        return int(cur.lastrowid)

    def query_facts(
        self,
        concept: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_conf: float = 0.0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        q = "SELECT * FROM semantic WHERE confidence >= ?"
        params: List[Any] = [min_conf]
        if concept:
            q += " AND concept LIKE ?"
            params.append(f"%{concept}%")
        if agent_id:
            q += " AND agent_id = ?"
            params.append(agent_id)
        q += " ORDER BY confidence DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------ procedural
    def learn_skill(
        self,
        agent_id: str,
        skill_name: str,
        steps: List[Dict],
        description: Optional[str] = None,
        preconditions: Optional[Dict] = None,
        postconditions: Optional[Dict] = None,
    ) -> int:
        cur = self.db.execute(
            """INSERT INTO procedural (agent_id, skill_name, description, steps, preconditions, postconditions)
               VALUES (?,?,?,?,?,?)""",
            (
                agent_id,
                skill_name,
                description,
                json.dumps(steps),
                json.dumps(preconditions or {}),
                json.dumps(postconditions or {}),
            ),
        )
        self.db.commit()
        return int(cur.lastrowid)

    def get_skill(self, skill_name: str, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        q = "SELECT * FROM procedural WHERE skill_name = ?"
        params: List[Any] = [skill_name]
        if agent_id:
            q += " AND agent_id = ?"
            params.append(agent_id)
        q += " ORDER BY success_rate DESC, execution_count DESC LIMIT 1"
        row = self.db.execute(q, params).fetchone()
        return dict(row) if row else None

    def list_skills(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        q = "SELECT * FROM procedural WHERE 1=1"
        params: List[Any] = []
        if agent_id:
            q += " AND agent_id = ?"
            params.append(agent_id)
        q += " ORDER BY success_rate DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def record_skill_result(self, skill_id: int, success: bool) -> None:
        self.db.execute(
            """UPDATE procedural SET
               success_rate = (success_rate * execution_count + ?) / (execution_count + 1),
               execution_count = execution_count + 1
               WHERE id = ?""",
            (1.0 if success else 0.0, skill_id),
        )
        self.db.commit()

    # ------------------------------------------------------------------ orgs
    def save_org(self, org_id: str, spec: Dict) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO orgs (id, spec) VALUES (?,?)",
            (org_id, json.dumps(spec)),
        )
        self.db.commit()

    def load_org(self, org_id: str) -> Optional[Dict[str, Any]]:
        row = self.db.execute("SELECT spec FROM orgs WHERE id = ?", (org_id,)).fetchone()
        return json.loads(row["spec"]) if row else None

    def list_orgs(self) -> List[Dict[str, Any]]:
        rows = self.db.execute("SELECT id, created_at FROM orgs ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- search
    def keyword_search(self, text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Naive lexical search across episodic content + semantic facts."""
        tokens = [t for t in re.split(r"\W+", text.lower()) if t]
        if not tokens:
            return []
        like = "%" + "%".join(tokens[:3]) + "%"
        out: List[Dict[str, Any]] = []
        for r in self.db.execute(
            "SELECT 'episodic' AS kind, id, content AS text FROM episodic WHERE lower(content) LIKE ? ORDER BY id DESC LIMIT ?",
            (like, limit),
        ):
            out.append(dict(r))
        for r in self.db.execute(
            "SELECT 'semantic' AS kind, id, fact AS text FROM semantic WHERE lower(fact) LIKE ? LIMIT ?",
            (like, limit),
        ):
            out.append(dict(r))
        return out

    # ---------------------------------------------------------------- stats
    def stats(self) -> Dict[str, int]:
        counts = {}
        for table in ("episodic", "semantic", "procedural", "orgs"):
            counts[table] = self.db.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        return counts


_singleton: Optional[MemoryFabric] = None


def get_memory_fabric(base_path: str | Path = DEFAULT_BASE) -> MemoryFabric:
    global _singleton
    if _singleton is None:
        _singleton = MemoryFabric(base_path)
    return _singleton


if __name__ == "__main__":
    m = get_memory_fabric()
    m.remember("test-agent", "observation", "Agent Genesis memory fabric works")
    m.learn_fact("agent-genesis", "memory fabric is operational")
    m.learn_skill("test-agent", "echo", [{"tool": "echo", "params": {"text": "hi"}}])
    print("Stats:", m.stats())
    print("Recall:", m.recall(agent_id="test-agent", limit=5))
    print("Facts:", m.query_facts("agent-genesis"))
    print("Skills:", m.list_skills("test-agent"))
    print("Search 'memory':", m.keyword_search("memory fabric works"))
    print("OK")
