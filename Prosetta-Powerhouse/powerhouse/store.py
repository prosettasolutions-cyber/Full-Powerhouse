from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CompanyStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=20)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                objective TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                phase TEXT NOT NULL DEFAULT 'Discovery',
                priority TEXT NOT NULL DEFAULT 'High',
                progress INTEGER NOT NULL DEFAULT 0,
                health TEXT NOT NULL DEFAULT 'Strong',
                milestone TEXT NOT NULL DEFAULT '',
                blocker TEXT NOT NULL DEFAULT 'None',
                owner TEXT NOT NULL DEFAULT 'Ritu',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Sleeping',
                project_id TEXT,
                memory_policy TEXT NOT NULL DEFAULT '',
                last_update TEXT NOT NULL DEFAULT '',
                progress INTEGER NOT NULL DEFAULT 0,
                signal TEXT NOT NULL DEFAULT 'Ready',
                dependencies TEXT NOT NULL DEFAULT 'None',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                agent_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Planned',
                priority TEXT NOT NULL DEFAULT 'Medium',
                deliverable_path TEXT,
                acceptance TEXT NOT NULL DEFAULT '{}',
                result TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(agent_id) REFERENCES agents(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                scope_type TEXT NOT NULL,
                scope_id TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                reuse_notes TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'Ritu',
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                task_id TEXT,
                path TEXT NOT NULL,
                version INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reference_files (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                media_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS training_sessions (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                objective TEXT NOT NULL,
                category TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_id TEXT,
                status TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                question TEXT NOT NULL DEFAULT '',
                module_id TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS intelligence_modules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                version INTEGER NOT NULL,
                path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope_type, scope_id)",
            "CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_training_created ON training_sessions(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_modules_name_version ON intelligence_modules(name, version DESC)",
        ]
        with self.connection() as connection:
            for statement in statements:
                connection.execute(statement)
            task_columns = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()}
            if "acceptance" not in task_columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN acceptance TEXT NOT NULL DEFAULT '{}'")
            project_columns = {row["name"] for row in connection.execute("PRAGMA table_info(projects)").fetchall()}
            for name, definition in {
                "priority": "TEXT NOT NULL DEFAULT 'High'",
                "progress": "INTEGER NOT NULL DEFAULT 0",
                "health": "TEXT NOT NULL DEFAULT 'Strong'",
                "milestone": "TEXT NOT NULL DEFAULT ''",
                "blocker": "TEXT NOT NULL DEFAULT 'None'",
                "owner": "TEXT NOT NULL DEFAULT 'Ritu'",
            }.items():
                if name not in project_columns:
                    connection.execute(f"ALTER TABLE projects ADD COLUMN {name} {definition}")
            agent_columns = {row["name"] for row in connection.execute("PRAGMA table_info(agents)").fetchall()}
            for name, definition in {
                "progress": "INTEGER NOT NULL DEFAULT 0",
                "signal": "TEXT NOT NULL DEFAULT 'Ready'",
                "dependencies": "TEXT NOT NULL DEFAULT 'None'",
            }.items():
                if name not in agent_columns:
                    connection.execute(f"ALTER TABLE agents ADD COLUMN {name} {definition}")

    @staticmethod
    def new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> None:
        with self.connection() as connection:
            connection.execute(sql, parameters)

    def one(self, sql: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(sql, parameters).fetchone()
        return dict(row) if row else None

    def all(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def add_event(self, kind: str, summary: str, payload: dict[str, Any] | None = None) -> None:
        self.execute(
            "INSERT INTO events(kind, summary, payload, created_at) VALUES(?,?,?,?)",
            (kind, summary, json.dumps(payload or {}, ensure_ascii=False), utc_now()),
        )

    def add_conversation(self, session_id: str, role: str, content: str) -> None:
        self.execute(
            "INSERT INTO conversations(session_id, role, content, created_at) VALUES(?,?,?,?)",
            (session_id, role, content, utc_now()),
        )

    def recent_conversation(self, session_id: str, limit: int = 12) -> list[dict[str, Any]]:
        rows = self.all(
            "SELECT role, content FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        return list(reversed(rows))

    def create_project(self, name: str, slug: str, objective: str, phase: str = "Discovery") -> dict[str, Any]:
        existing = self.one("SELECT * FROM projects WHERE lower(name)=lower(?)", (name,))
        if existing:
            return existing
        now = utc_now()
        project_id = self.new_id("project")
        self.execute(
            "INSERT INTO projects(id,name,slug,objective,status,phase,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (project_id, name, slug, objective, "Active", phase, now, now),
        )
        project = self.one("SELECT * FROM projects WHERE id=?", (project_id,))
        self.add_event("project_created", f"Project created: {name}", {"project_id": project_id})
        return project or {}

    def find_project(self, reference: str | None) -> dict[str, Any] | None:
        if reference:
            found = self.one(
                "SELECT * FROM projects WHERE id=? OR lower(name)=lower(?) OR slug=?",
                (reference, reference, reference),
            )
            if found:
                return found
        return self.one("SELECT * FROM projects WHERE status='Active' ORDER BY updated_at DESC LIMIT 1")

    def update_project(self, reference: str, updates: dict[str, Any]) -> dict[str, Any]:
        project = self.find_project(reference)
        if not project:
            raise ValueError(f"Project not found: {reference}")
        allowed = {"name", "objective", "status", "phase", "priority", "progress", "health", "milestone", "blocker", "owner"}
        clean = {key: value for key, value in updates.items() if key in allowed and value is not None}
        if "progress" in clean:
            clean["progress"] = max(0, min(100, int(clean["progress"])))
        for key in allowed - {"progress"}:
            if key in clean:
                clean[key] = str(clean[key]).strip()
        if not clean:
            raise ValueError("No supported project updates were supplied.")
        clean["updated_at"] = utc_now()
        assignments = ",".join(f"{key}=?" for key in clean)
        self.execute(
            f"UPDATE projects SET {assignments} WHERE id=?",
            (*clean.values(), project["id"]),
        )
        updated = self.one("SELECT * FROM projects WHERE id=?", (project["id"],)) or {}
        self.add_event(
            "project_updated",
            f"Project updated: {updated.get('name', project['name'])}",
            {"project_id": project["id"], "changes": clean},
        )
        return updated

    def create_agent(
        self,
        name: str,
        role: str,
        capabilities: list[str],
        project_id: str | None,
        status: str = "Active",
        memory_policy: str = "",
    ) -> dict[str, Any]:
        existing = self.one("SELECT * FROM agents WHERE lower(name)=lower(?)", (name,))
        now = utc_now()
        if existing:
            self.execute(
                "UPDATE agents SET role=?,capabilities=?,project_id=?,status=?,memory_policy=?,updated_at=? WHERE id=?",
                (role, json.dumps(capabilities), project_id, status, memory_policy, now, existing["id"]),
            )
            return self.one("SELECT * FROM agents WHERE id=?", (existing["id"],)) or {}
        agent_id = self.new_id("agent")
        self.execute(
            "INSERT INTO agents(id,name,role,capabilities,status,project_id,memory_policy,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (agent_id, name, role, json.dumps(capabilities), status, project_id, memory_policy, now, now),
        )
        agent = self.one("SELECT * FROM agents WHERE id=?", (agent_id,))
        self.add_event("agent_hired", f"Agent hired: {name}", {"agent_id": agent_id, "project_id": project_id})
        return agent or {}

    def find_agent(self, reference: str | None) -> dict[str, Any] | None:
        if not reference:
            return None
        return self.one("SELECT * FROM agents WHERE id=? OR lower(name)=lower(?)", (reference, reference))

    def update_agent(self, reference: str, updates: dict[str, Any]) -> dict[str, Any]:
        agent = self.find_agent(reference)
        if not agent:
            raise ValueError(f"Agent not found: {reference}")
        allowed = {"name", "role", "capabilities", "status", "project_id", "memory_policy", "last_update", "progress", "signal", "dependencies"}
        clean = {key: value for key, value in updates.items() if key in allowed and value is not None}
        if "progress" in clean:
            clean["progress"] = max(0, min(100, int(clean["progress"])))
        if "capabilities" in clean:
            capabilities = clean["capabilities"]
            if not isinstance(capabilities, list):
                raise ValueError("Agent capabilities must be a list.")
            clean["capabilities"] = json.dumps([str(item).strip() for item in capabilities if str(item).strip()])
        for key in allowed - {"progress", "capabilities"}:
            if key in clean:
                clean[key] = str(clean[key]).strip()
        if not clean:
            raise ValueError("No supported agent updates were supplied.")
        clean["updated_at"] = utc_now()
        assignments = ",".join(f"{key}=?" for key in clean)
        self.execute(
            f"UPDATE agents SET {assignments} WHERE id=?",
            (*clean.values(), agent["id"]),
        )
        updated = self.one("SELECT * FROM agents WHERE id=?", (agent["id"],)) or {}
        self.add_event(
            "agent_updated",
            f"Agent updated: {updated.get('name', agent['name'])}",
            {"agent_id": agent["id"], "project_id": updated.get("project_id"), "changes": clean},
        )
        return updated

    def set_agent_status(self, reference: str, status: str) -> dict[str, Any]:
        agent = self.find_agent(reference)
        if not agent:
            raise ValueError(f"Agent not found: {reference}")
        self.execute("UPDATE agents SET status=?,updated_at=? WHERE id=?", (status, utc_now(), agent["id"]))
        self.add_event("agent_status", f"{agent['name']} is now {status}.", {"agent_id": agent["id"]})
        return self.one("SELECT * FROM agents WHERE id=?", (agent["id"],)) or {}

    def create_task(
        self,
        project_id: str,
        title: str,
        description: str,
        agent_id: str | None,
        priority: str = "Medium",
        deliverable_path: str | None = None,
        acceptance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        task_id = self.new_id("task")
        self.execute(
            "INSERT INTO tasks(id,project_id,agent_id,title,description,status,priority,deliverable_path,acceptance,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (task_id, project_id, agent_id, title, description, "Planned", priority, deliverable_path, json.dumps(acceptance or {}), now, now),
        )
        self.add_event("task_created", f"Task created: {title}", {"task_id": task_id, "agent_id": agent_id})
        return self.one("SELECT * FROM tasks WHERE id=?", (task_id,)) or {}

    def update_task(self, task_id: str, status: str, result: str = "") -> dict[str, Any]:
        task = self.one("SELECT * FROM tasks WHERE id=?", (task_id,))
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        self.execute("UPDATE tasks SET status=?,result=?,updated_at=? WHERE id=?", (status, result, utc_now(), task_id))
        self.add_event("task_status", f"{task['title']} moved to {status}.", {"task_id": task_id})
        return self.one("SELECT * FROM tasks WHERE id=?", (task_id,)) or {}

    def update_task_record(self, reference: str, updates: dict[str, Any]) -> dict[str, Any]:
        task = self.one("SELECT * FROM tasks WHERE id=? OR lower(title)=lower(?)", (reference, reference))
        if not task:
            raise ValueError(f"Task not found: {reference}")
        allowed = {"title", "description", "status", "priority", "agent_id", "deliverable_path", "result"}
        clean = {key: value for key, value in updates.items() if key in allowed and value is not None}
        for key in clean:
            clean[key] = str(clean[key]).strip()
        if not clean:
            raise ValueError("No supported task updates were supplied.")
        clean["updated_at"] = utc_now()
        assignments = ",".join(f"{key}=?" for key in clean)
        self.execute(
            f"UPDATE tasks SET {assignments} WHERE id=?",
            (*clean.values(), task["id"]),
        )
        updated = self.one("SELECT * FROM tasks WHERE id=?", (task["id"],)) or {}
        self.add_event(
            "task_updated",
            f"Task updated: {updated.get('title', task['title'])}",
            {"task_id": task["id"], "project_id": task["project_id"], "changes": clean},
        )
        return updated

    def add_memory(
        self,
        scope_type: str,
        scope_id: str | None,
        title: str,
        content: str,
        reuse_notes: str = "",
        source: str = "Ritu",
    ) -> dict[str, Any]:
        memory_id = self.new_id("memory")
        self.execute(
            "INSERT INTO memories(id,scope_type,scope_id,title,content,reuse_notes,source,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (memory_id, scope_type, scope_id, title, content, reuse_notes, source, utc_now()),
        )
        self.add_event("memory_added", f"Memory captured: {title}", {"memory_id": memory_id})
        return self.one("SELECT * FROM memories WHERE id=?", (memory_id,)) or {}

    def find_matching_memory(
        self,
        scope_type: str,
        scope_id: str | None,
        title: str,
        content: str,
    ) -> dict[str, Any] | None:
        return self.one(
            """
            SELECT * FROM memories
            WHERE scope_type=?
              AND ((scope_id IS NULL AND ? IS NULL) OR scope_id=?)
              AND (lower(title)=lower(?) OR content=?)
            ORDER BY created_at DESC LIMIT 1
            """,
            (scope_type, scope_id, scope_id, title, content),
        )

    def relevant_memories(self, project_id: str | None, agent_id: str | None, limit: int = 20) -> list[dict[str, Any]]:
        return self.all(
            """
            SELECT * FROM memories
            WHERE scope_type='global'
               OR (scope_type='project' AND scope_id=?)
               OR (scope_type='agent' AND scope_id=?)
            ORDER BY created_at DESC LIMIT ?
            """,
            (project_id, agent_id, limit),
        )

    def add_artifact(
        self,
        project_id: str,
        task_id: str | None,
        path: str,
        version: int,
        sha256: str,
        summary: str = "",
    ) -> None:
        self.execute(
            "INSERT INTO artifacts(id,project_id,task_id,path,version,sha256,summary,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (self.new_id("artifact"), project_id, task_id, path, version, sha256, summary, utc_now()),
        )
        self.add_event("artifact_written", f"Artifact written: {path}", {"project_id": project_id, "task_id": task_id})

    def add_reference(self, project_id: str | None, name: str, path: str, media_type: str, sha256: str) -> dict[str, Any]:
        reference_id = self.new_id("reference")
        self.execute(
            "INSERT INTO reference_files(id,project_id,name,path,media_type,sha256,created_at) VALUES(?,?,?,?,?,?,?)",
            (reference_id, project_id, name, path, media_type, sha256, utc_now()),
        )
        self.add_event("reference_uploaded", f"Reference uploaded: {name}", {"reference_id": reference_id})
        return self.one("SELECT * FROM reference_files WHERE id=?", (reference_id,)) or {}

    def start_training(
        self,
        topic: str,
        objective: str,
        category: str,
        scope_type: str,
        scope_id: str | None,
    ) -> dict[str, Any]:
        session_id = self.new_id("training")
        self.execute(
            """
            INSERT INTO training_sessions(
                id,topic,objective,category,scope_type,scope_id,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (session_id, topic, objective, category, scope_type, scope_id, "Learning", utc_now()),
        )
        self.add_event("training_started", f"Training started: {topic}", {"training_id": session_id})
        return self.one("SELECT * FROM training_sessions WHERE id=?", (session_id,)) or {}

    def finish_training(
        self,
        session_id: str,
        status: str,
        summary: str,
        question: str = "",
        module_id: str | None = None,
    ) -> dict[str, Any]:
        self.execute(
            """
            UPDATE training_sessions
            SET status=?,summary=?,question=?,module_id=?,completed_at=?
            WHERE id=?
            """,
            (status, summary, question, module_id, utc_now(), session_id),
        )
        event_kind = {
            "Completed": "training_completed",
            "Needs Input": "training_needs_input",
            "Failed": "training_failed",
        }.get(status, "training_updated")
        self.add_event(
            event_kind,
            f"Training {status.lower()}: {summary}",
            {"training_id": session_id, "module_id": module_id},
        )
        return self.one("SELECT * FROM training_sessions WHERE id=?", (session_id,)) or {}

    def add_intelligence_module(
        self,
        name: str,
        category: str,
        description: str,
        version: int,
        path: str,
    ) -> dict[str, Any]:
        module_id = self.new_id("module")
        now = utc_now()
        self.execute(
            """
            INSERT INTO intelligence_modules(
                id,name,category,description,version,path,status,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (module_id, name, category, description, version, path, "Active", now, now),
        )
        self.add_event(
            "intelligence_added",
            f"Intelligence module added: {name} v{version}",
            {"module_id": module_id, "path": path},
        )
        return self.one("SELECT * FROM intelligence_modules WHERE id=?", (module_id,)) or {}

    def training_status(self) -> dict[str, Any]:
        sessions = self.all("SELECT * FROM training_sessions ORDER BY created_at DESC LIMIT 50")
        modules = self.all("SELECT * FROM intelligence_modules ORDER BY created_at DESC LIMIT 50")
        memory_count = self.one("SELECT COUNT(*) AS count FROM memories") or {"count": 0}
        return {
            "sessions": sessions,
            "modules": modules,
            "counts": {
                "sessions": len(sessions),
                "completed": sum(1 for session in sessions if session["status"] == "Completed"),
                "needs_input": sum(1 for session in sessions if session["status"] == "Needs Input"),
                "modules": len(modules),
                "memories": memory_count["count"],
            },
        }

    @staticmethod
    def _json_value(value: Any, fallback: Any) -> Any:
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value or "")
        except (json.JSONDecodeError, TypeError):
            return fallback

    def portal_state(self) -> dict[str, Any]:
        raw_projects = self.all("SELECT * FROM projects ORDER BY updated_at DESC")
        raw_agents = self.all("SELECT * FROM agents ORDER BY status='Active' DESC, updated_at DESC")
        raw_tasks = self.all("SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 200")
        raw_memories = self.all("SELECT * FROM memories ORDER BY created_at DESC LIMIT 200")
        raw_artifacts = self.all("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT 200")
        raw_references = self.all("SELECT * FROM reference_files ORDER BY created_at DESC LIMIT 100")
        raw_events = self.all("SELECT * FROM events ORDER BY id DESC LIMIT 150")
        training = self.one("SELECT COUNT(*) AS count FROM training_sessions") or {"count": 0}
        modules = self.one("SELECT COUNT(*) AS count FROM intelligence_modules") or {"count": 0}
        project_by_id = {item["id"]: item for item in raw_projects}
        agent_by_id = {item["id"]: item for item in raw_agents}
        tasks_by_project: dict[str, list[dict[str, Any]]] = {}
        tasks_by_agent: dict[str, list[dict[str, Any]]] = {}
        progress_by_status = {
            "Proposed": 5,
            "Planned": 10,
            "In Progress": 50,
            "Review": 80,
            "Blocked": 45,
            "Completed": 100,
            "Archived": 100,
        }
        tasks = []
        for task in raw_tasks:
            normalized = {
                **task,
                "project": task["project_id"],
                "agent": task["agent_id"],
                "project_name": project_by_id.get(task["project_id"], {}).get("name", "Unknown project"),
                "agent_name": agent_by_id.get(task["agent_id"], {}).get("name", "Ritu"),
                "progress": progress_by_status.get(task["status"], 0),
                "acceptance": self._json_value(task.get("acceptance"), {}),
            }
            tasks.append(normalized)
            tasks_by_project.setdefault(task["project_id"], []).append(normalized)
            if task.get("agent_id"):
                tasks_by_agent.setdefault(task["agent_id"], []).append(normalized)

        artifacts_by_project: dict[str, list[str]] = {}
        for artifact in raw_artifacts:
            artifacts_by_project.setdefault(artifact["project_id"], []).append(artifact["path"])

        projects = []
        for project in raw_projects:
            project_tasks = tasks_by_project.get(project["id"], [])
            project_agents = [agent["id"] for agent in raw_agents if agent.get("project_id") == project["id"]]
            projects.append(
                {
                    **project,
                    "description": project["objective"],
                    "type": "Company Program",
                    "agents": project_agents,
                    "files": artifacts_by_project.get(project["id"], [])[:20],
                    "risks": [] if project.get("blocker") in {"", "None"} else [project["blocker"]],
                    "last": project["updated_at"],
                    "open_tasks": sum(1 for task in project_tasks if task["status"] not in {"Completed", "Archived"}),
                }
            )

        agents = []
        for agent in raw_agents:
            agent_tasks = tasks_by_agent.get(agent["id"], [])
            current = next(
                (task for task in agent_tasks if task["status"] not in {"Completed", "Archived"}),
                agent_tasks[0] if agent_tasks else None,
            )
            agents.append(
                {
                    **agent,
                    "project": agent.get("project_id"),
                    "capabilities": self._json_value(agent.get("capabilities"), []),
                    "task": current["title"] if current else (agent.get("last_update") or "Available for assignment"),
                    "last": agent.get("updated_at"),
                }
            )

        memories = [
            {
                **memory,
                "summary": memory["content"],
                "category": memory["scope_type"].title(),
                "confidence": 100 if memory["source"] in {"Ritu", "System charter", "Training Room"} else 92,
                "created": memory["created_at"],
                "used": "Available",
            }
            for memory in raw_memories
        ]
        events = []
        for event in raw_events:
            payload = self._json_value(event.get("payload"), {})
            events.append(
                {
                    **event,
                    "payload": payload,
                    "type": event["kind"].replace("_", " ").title(),
                    "text": event["summary"],
                    "time": event["created_at"],
                    "project": payload.get("project_id"),
                    "agent": payload.get("agent_id") or "Ritu",
                    "priority": "High" if any(word in event["kind"] for word in ("failed", "blocked", "approval")) else "Medium",
                }
            )
        revision = raw_events[0]["id"] if raw_events else 0
        return {
            "projects": projects,
            "agents": agents,
            "tasks": tasks,
            "memories": memories,
            "artifacts": raw_artifacts,
            "references": raw_references,
            "counts": {
                "projects": len(projects),
                "agents": len(agents),
                "active_agents": sum(1 for agent in agents if agent["status"] == "Active"),
                "sleeping_agents": sum(1 for agent in agents if agent["status"] == "Sleeping"),
                "open_tasks": sum(1 for task in tasks if task["status"] not in {"Completed", "Archived"}),
                "memories": len(memories),
                "artifacts": len(raw_artifacts),
                "references": len(raw_references),
                "training_sessions": training["count"],
                "intelligence_modules": modules["count"],
            },
            "events": events,
            "activities": events,
            "revision": revision,
            "verified_at": utc_now(),
        }

    def status(self) -> dict[str, Any]:
        return self.portal_state()
