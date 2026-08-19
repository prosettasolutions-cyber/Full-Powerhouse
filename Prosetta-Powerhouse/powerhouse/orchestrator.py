from __future__ import annotations

import ast
import json
from pprint import pformat
from typing import Any

from .config import (
    DATABASE_PATH,
    OLLAMA_DEEP_MODEL,
    OLLAMA_FAST_MODEL,
    OLLAMA_URL,
    RITU_ROOT,
    ensure_layout,
    slugify,
)
from .ollama_client import OllamaClient
from .store import CompanyStore
from .workspace import PowerhouseWorkspace


PLANNER_SYSTEM = """
You are Ritu, Prashant's private personal eCEO and operating intelligence.
Your job is to discuss project ideas, identify missing requirements, choose the next useful step,
hire only the specialist agents needed, assign work, preserve reusable memory, and report status.

You operate only inside a local Powerhouse workspace. You may create project files but never run
shell commands, install software, delete user files, expose secrets, or write outside the workspace.
Removing an agent always means archiving it. Sleeping is preferred when an agent is temporarily idle.
Ask focused questions before acting when the objective, users, deliverables, constraints, or success
criteria are unclear. Do not pretend work is complete when it is not.

Return one JSON object:
{
  "response": "what you want to tell Prashant",
  "needs_input": false,
  "actions": [
    {"type": "create_project", "args": {"name": "...", "objective": "...", "phase": "Discovery"}},
    {"type": "update_project", "args": {"project": "id or name", "description": "...", "phase": "...", "status": "...", "priority": "...", "progress": 0, "health": "...", "milestone": "...", "blocker": "...", "owner": "..."}},
    {"type": "hire_agent", "args": {"name": "...", "role": "...", "capabilities": ["..."], "project": "...", "status": "Active"}},
    {"type": "update_agent", "args": {"agent": "id or name", "role": "...", "capabilities": ["..."], "status": "...", "project": "id or name", "progress": 0, "signal": "...", "dependencies": "...", "last_update": "...", "memory_policy": "..."}},
    {"type": "sleep_agent", "args": {"agent": "..."}},
    {"type": "wake_agent", "args": {"agent": "..."}},
    {"type": "archive_agent", "args": {"agent": "..."}},
    {"type": "create_task", "args": {"project": "...", "agent": "...", "title": "...", "description": "...", "priority": "High", "deliverable_path": "src/module.py", "acceptance": {"required_files": ["src/module.py"], "required_strings": ["exact required value"], "required_python_symbols": ["function_name"], "required_return_mapping": {"function_name": {"key": "exact value"}}}, "auto_run": false}},
    {"type": "update_task", "args": {"task": "id or exact title", "status": "...", "priority": "...", "description": "...", "agent": "id or name"}},
    {"type": "run_task", "args": {"task_id": "...", "sleep_after": true}},
    {"type": "write_file", "args": {"scope": "project|portal", "project": "...", "path": "src/module.py", "content": "...", "summary": "..."}},
    {"type": "patch_file", "args": {"scope": "project|portal", "project": "...", "path": "...", "find": "exact existing text", "replace": "replacement text", "summary": "..."}},
    {"type": "add_memory", "args": {"scope": "global|project|agent", "scope_id": "...", "title": "...", "content": "...", "reuse_notes": "..."}},
    {"type": "train_ritu", "args": {"topic": "...", "objective": "...", "category": "Strategy|Leadership|Operations|Research|Memory|Technical", "scope": "global|project|agent", "source_notes": "..."}}
  ]
}

Use at most 8 actions. If you need Prashant's answer, set needs_input=true and actions=[].
Use run_task only with a known task id. For new tasks, set auto_run=true when immediate execution is safe.
Every implementation task must include concrete acceptance criteria. Put exact requested names and values
in required_strings, requested Python functions/classes in required_python_symbols, and paths in required_files.
When a Python function must return exact constant fields, put them in required_return_mapping.
When Prashant changes a project description, phase, progress, milestone, blocker, owner, agent status,
agent learning update, or task status, use the matching update action. The website reads these records
directly, so never claim the portal was updated unless the action succeeded and returned a verified record.
Use patch_file for small changes to an existing file. Portal source changes are allowed only from the
Boardroom after explicit approval. Never edit secrets, environment files, Git internals, history, or backups.
"""


AGENT_SYSTEM = """
You are a specialist agent working for Ritu. Complete the assigned task using the supplied project,
memory, file index, and reference context. Produce practical, reusable work. You cannot execute code
or access anything outside the project workspace.
Treat the task description and requested deliverable path as an acceptance contract. Do not add
unrequested behavior, substitute different fields, or claim completion when a requirement is missing.

Return one JSON object:
{
  "summary": "concise completion update",
  "files": [{"path": "relative/path.py", "content": "complete file content", "summary": "purpose"}],
  "memories": [{"title": "lesson", "content": "what was learned", "reuse_notes": "how to reuse it"}],
  "needs_input": false,
  "question": ""
}
If blocked, return no files, needs_input=true, and one precise question.
"""

QA_SYSTEM = """
You are Ritu's QA Agent. Review a specialist's proposed files against the exact task description and
deliverable path. Do not approve merely because code is syntactically plausible. Check every explicit
field, value, constraint, and requested file. Return one JSON object:
{
  "pass": true,
  "issues": [],
  "summary": "acceptance result",
  "corrected_files": [{"path": "relative/path.py", "content": "complete corrected content", "summary": "correction"}]
}
When any requirement is missing or contradicted, set pass=false and provide complete corrected files.
Do not introduce unrelated behavior.
"""

TRAINING_SYSTEM = """
You are Ritu's Training Intelligence. Convert Prashant's training request into durable, concise,
reusable operating intelligence. Distinguish facts, principles, procedures, guardrails, and open
questions. Never claim a fact is verified when no source was supplied. Never store private
chain-of-thought, credentials, or secrets.

Return one JSON object:
{
  "needs_input": false,
  "question": "",
  "summary": "what Ritu learned and how it improves her",
  "module_name": "short durable intelligence name",
  "category": "Strategy|Leadership|Operations|Research|Memory|Technical",
  "knowledge": ["verified or user-taught knowledge"],
  "principles": ["decision principles"],
  "procedures": ["step-by-step reusable procedures"],
  "guardrails": ["limits and approval boundaries"],
  "verification_questions": ["questions to check correct application"],
  "memories": [
    {"title": "memory title", "content": "durable memory", "reuse_notes": "when and how agents should reuse it"}
  ]
}

If the request is too vague to learn safely, set needs_input=true, ask one focused question, and do
not invent knowledge. Keep each list practical and concise.
"""

ROOM_POLICIES = {
    "command": (
        "This is the Command Center. Answer company-wide and cross-project questions, help set overall "
        "direction, and coordinate new missions. Do not narrow the conversation to one project unless asked."
    ),
    "company": (
        "This is the CEO Company room. Prioritize factual status reporting from the supplied live company "
        "state: projects, programs, agents, tasks, blockers, workload, progress, and next actions."
    ),
    "training": (
        "This is Ritu's Training Room. Discuss what capability, memory, procedure, guardrail, or intelligence "
        "should be added. Explain the proposed change and ask Prashant's permission before returning a "
        "train_ritu action. Return train_ritu only after explicit approval in the current user message."
    ),
    "boardroom": (
        "This is the Boardroom for consequential company, project, agent, and intelligence decisions. "
        "Present the decision, alternatives, evidence, risks, recommendation, and approval required. "
        "Do not execute consequential actions until Prashant explicitly approves."
    ),
    "project": (
        "This is a dedicated Project Room. Stay within the selected project context. Answer project status, "
        "requirements, risks, files, tasks, agents, blockers, and next-step questions."
    ),
    "agents": (
        "This is the overall Agent Organization room. Discuss staffing, workload, performance, coordination, "
        "agent issues, learning, sleeping/waking, and capability gaps across all agents."
    ),
    "agent": (
        "This is a direct Agent Room. Respond as the selected specialist agent, using its name, role, task, "
        "status, and project context. Report work status, blockers, issues, changes made, validation, and "
        "learning. Escalate company-level decisions to Ritu rather than pretending the agent has CEO authority."
    ),
}


class RituOrchestrator:
    def __init__(self):
        ensure_layout()
        self.store = CompanyStore(DATABASE_PATH)
        self.workspace = PowerhouseWorkspace(self.store)
        self.fast_ollama = OllamaClient(OLLAMA_URL, OLLAMA_FAST_MODEL)
        self.deep_ollama = OllamaClient(OLLAMA_URL, OLLAMA_DEEP_MODEL)
        self.ollama = self.fast_ollama
        self.bootstrap()

    def bootstrap(self) -> None:
        project = self.store.create_project(
            "Ritu Autonomous Company",
            slugify("Ritu Autonomous Company"),
            (
                "Build Ritu into Prashant's local personal eCEO: discuss requirements, determine next steps, "
                "hire and sleep specialist agents, delegate tasks, preserve reusable memory, create project "
                "artifacts, process references, and provide truthful status updates."
            ),
            "Foundation",
        )
        self.workspace.initialize_project(project)
        agents = [
            (
                "Ritu",
                "Personal eCEO and central orchestrator",
                ["requirements", "planning", "delegation", "status reporting", "memory governance"],
                "Active",
            ),
            (
                "Architecture Agent",
                "Designs modular local-first systems and safety boundaries",
                ["system architecture", "interfaces", "risk analysis"],
                "Active",
            ),
            (
                "Python Builder",
                "Creates maintainable Python modules and tests",
                ["python", "sqlite", "apis", "testing"],
                "Active",
            ),
            (
                "Research Agent",
                "Collects and cites external facts for project decisions",
                ["research", "source evaluation", "data extraction"],
                "Sleeping",
            ),
            (
                "Memory Curator",
                "Converts project experience into reusable organizational memory",
                ["knowledge management", "lessons learned", "retrieval"],
                "Sleeping",
            ),
            (
                "QA Agent",
                "Validates deliverables, regressions, and completion claims",
                ["quality assurance", "testing", "acceptance criteria"],
                "Sleeping",
            ),
        ]
        for name, role, capabilities, status in agents:
            if not self.store.find_agent(name):
                self.store.create_agent(
                    name,
                    role,
                    capabilities,
                    project["id"],
                    status,
                    "Keep decisions, failures, fixes, and reusable patterns; never store private chain-of-thought.",
                )

        seed_tasks = [
            ("Define Ritu autonomy charter", "Document authority boundaries, approval gates, and audit rules.", "Architecture Agent", "Critical", "docs/autonomy_charter.md"),
            ("Build persistent company intelligence", "Implement projects, agents, tasks, memories, artifacts, references, and events.", "Python Builder", "Critical", "src/company_intelligence.py"),
            ("Design adaptive agent lifecycle", "Define hiring, teaching, waking, sleeping, and recoverable archiving.", "Architecture Agent", "High", "docs/agent_lifecycle.md"),
            ("Build reusable memory loop", "Define how issues, changes, fixes, and reuse guidance become scoped memory.", "Memory Curator", "High", "docs/memory_loop.md"),
            ("Define research and evidence workflow", "Design local screen reading, explicit URL research, citations, and reference retention.", "Research Agent", "High", "docs/research_workflow.md"),
        ]
        for title, description, agent_name, priority, deliverable in seed_tasks:
            exists = self.store.one("SELECT id FROM tasks WHERE project_id=? AND title=?", (project["id"], title))
            if not exists:
                agent = self.store.find_agent(agent_name)
                self.store.create_task(
                    project["id"],
                    title,
                    description,
                    agent["id"] if agent else None,
                    priority,
                    deliverable,
                    {"required_files": [deliverable]},
                )

        if not self.store.one("SELECT id FROM memories WHERE title='Local-first authority boundary'"):
            self.store.add_memory(
                "global",
                None,
                "Local-first authority boundary",
                "Ritu may autonomously manage agents, tasks, memory, and project files only inside the Powerhouse workspace.",
                "Require explicit approval before system changes, credentials, external publishing, purchases, or irreversible deletion.",
                "System charter",
            )
        if not self.store.one("SELECT id FROM memories WHERE title='Learning standard'"):
            self.store.add_memory(
                "global",
                None,
                "Learning standard",
                "Agents report the issue faced, change made, result, and reusable pattern after meaningful work.",
                "Share only scoped, relevant memory with future agents.",
                "System charter",
            )

    def health(self) -> dict[str, Any]:
        try:
            fast = self.fast_ollama.health()
            deep = self.deep_ollama.health()
            ollama = {
                "online": True,
                "version": fast.get("version"),
                "models": fast.get("models", []),
                "fast_model": OLLAMA_FAST_MODEL,
                "deep_model": OLLAMA_DEEP_MODEL,
                "routing": {
                    "training": OLLAMA_DEEP_MODEL,
                    "boardroom": OLLAMA_DEEP_MODEL,
                    "default": OLLAMA_FAST_MODEL,
                },
            }
        except Exception as error:
            ollama = {
                "online": False,
                "fast_model": OLLAMA_FAST_MODEL,
                "deep_model": OLLAMA_DEEP_MODEL,
                "error": str(error),
            }
        return {
            "ok": True,
            "service": "Ritu eCEO",
            "workspace": str(RITU_ROOT),
            "ollama": ollama,
            "counts": self.store.status()["counts"],
        }

    def status(self) -> dict[str, Any]:
        state = self.store.status()
        for project in state["projects"]:
            project["files"] = self.workspace.project_file_index(project, 300)
        state["counts"]["files"] = sum(len(project["files"]) for project in state["projects"])
        return {"ok": True, "workspace": str(RITU_ROOT), "portal_root": str(self.workspace.scope_root("portal")), **state}

    def list_files(self, scope: str, project_reference: str | None = None) -> dict[str, Any]:
        project = self.store.find_project(project_reference) if scope == "project" else None
        files = self.workspace.list_files(scope, project)
        return {
            "ok": True,
            "scope": scope,
            "project": project,
            "files": files,
            "count": len(files),
            "verified": True,
        }

    def read_file(self, scope: str, path: str, project_reference: str | None = None) -> dict[str, Any]:
        project = self.store.find_project(project_reference) if scope == "project" else None
        return self.workspace.read_text_file(scope, path, project)

    def write_file(
        self,
        scope: str,
        path: str,
        content: str,
        project_reference: str | None = None,
        summary: str = "Updated from localhost portal",
    ) -> dict[str, Any]:
        project = self.store.find_project(project_reference) if scope == "project" else None
        result = self.workspace.write_scoped_text(scope, path, content, project, summary)
        return {"ok": True, "verified": True, "file": result, "company": self.status()}

    def update_task_status(self, task_reference: str, status: str) -> dict[str, Any]:
        allowed = {"Proposed", "Planned", "In Progress", "Review", "Blocked", "Completed", "Archived"}
        if status not in allowed:
            raise ValueError(f"Unsupported task status: {status}")
        task = self.store.update_task_record(task_reference, {"status": status})
        return {
            "ok": True,
            "verified": True,
            "task": task,
            "company": self.status(),
        }

    def chat(
        self,
        message: str,
        session_id: str = "default",
        selected_context: dict[str, Any] | None = None,
        room: str = "command",
    ) -> dict[str, Any]:
        message = message.strip()
        if not message:
            raise ValueError("Message is required.")
        room = room if room in ROOM_POLICIES else "command"
        self.store.add_conversation(session_id, "user", message)
        status = self.store.status()
        compact = {
            "active_room": room,
            "projects": [{"id": p["id"], "name": p["name"], "phase": p["phase"], "status": p["status"]} for p in status["projects"]],
            "agents": [{"id": a["id"], "name": a["name"], "role": a["role"], "status": a["status"], "project_id": a["project_id"]} for a in status["agents"]],
            "tasks": [{"id": t["id"], "title": t["title"], "status": t["status"], "project_id": t["project_id"], "agent_id": t["agent_id"]} for t in status["tasks"][:30]],
            "selected_context": selected_context or {},
        }
        project_reference = str((selected_context or {}).get("project_id") or "")
        active_project = self.store.find_project(project_reference) if project_reference else None
        file_terms = ("file", "code", "folder", "workspace", "artifact", "document", "readme", "python", "website", "portal")
        if active_project and (room == "project" or any(term in message.casefold() for term in file_terms)):
            compact["project_workspace"] = self.workspace.file_context(active_project)
        if room == "boardroom" or any(term in message.casefold() for term in ("website", "portal", "frontend", "ui", "server.py", "app.js", "styles.css", "index.html")):
            compact["portal_source"] = self.workspace.portal_file_context(message)
        history = self.store.recent_conversation(session_id, 10)
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "system", "content": ROOM_POLICIES[room]},
            {"role": "system", "content": f"Current company state:\n{json.dumps(compact, ensure_ascii=False)}"},
            *history,
        ]
        model_client = self.deep_ollama if room in {"training", "boardroom"} else self.fast_ollama
        raw = model_client.chat(messages, json_mode=True, temperature=0.15)
        plan = self._parse_json(raw)
        response = str(plan.get("response") or "I have reviewed the request.")
        actions = plan.get("actions") if isinstance(plan.get("actions"), list) else []
        approval_terms = (
            "approve",
            "approved",
            "proceed",
            "go ahead",
            "begin training",
            "start training",
            "you have my permission",
            "permission granted",
        )
        explicitly_approved = any(term in message.casefold() for term in approval_terms)
        portal_file_actions = [
            action
            for action in actions
            if action.get("type") in {"write_file", "patch_file"}
            and isinstance(action.get("args"), dict)
            and action["args"].get("scope") == "portal"
        ]
        if portal_file_actions and room != "boardroom":
            actions = []
            plan["needs_input"] = True
            response += "\n\nPortal source changes must be reviewed and explicitly approved in the Boardroom."
        if room == "training" and any(action.get("type") == "train_ritu" for action in actions) and not explicitly_approved:
            actions = []
            plan["needs_input"] = True
            response += "\n\nNo training change has been applied yet. Approve or revise the proposal when you are ready."
        if room == "boardroom" and actions and not explicitly_approved:
            actions = []
            plan["needs_input"] = True
            response += "\n\nNo consequential action has been executed. The Boardroom is waiting for your explicit approval."
        outcomes = []
        if not plan.get("needs_input"):
            for action in actions[:8]:
                try:
                    outcomes.append(self._execute_action(action))
                except Exception as error:
                    outcomes.append({"type": action.get("type", "unknown"), "ok": False, "error": str(error)})
        completed = [outcome for outcome in outcomes if outcome.get("ok")]
        failed = [outcome for outcome in outcomes if not outcome.get("ok")]
        if completed:
            response += "\n\nExecuted: " + "; ".join(outcome["summary"] for outcome in completed)
        if failed:
            response += "\n\nNeeds attention: " + "; ".join(outcome.get("error", "action failed") for outcome in failed)
        self.store.add_conversation(session_id, "assistant", response)
        self.store.add_event("ritu_update", response[:500], {"room": room, "actions": outcomes})
        return {
            "response": response,
            "reply": response,
            "actions": outcomes,
            "needs_input": bool(plan.get("needs_input")),
            "room": room,
            "model": model_client.model,
            "company": self.status(),
        }

    def upload_reference(
        self,
        filename: str,
        encoded_data: str,
        media_type: str,
        project_reference: str | None = None,
    ) -> dict[str, Any]:
        project = self.store.find_project(project_reference)
        reference = self.workspace.save_reference(project, filename, encoded_data, media_type)
        return {"ok": True, "reference": reference, "project": project}

    def training_status(self) -> dict[str, Any]:
        return {"ok": True, "workspace": str(RITU_ROOT), **self.store.training_status()}

    def train(
        self,
        topic: str,
        objective: str,
        category: str = "Operations",
        scope: str = "global",
        source_notes: str = "",
    ) -> dict[str, Any]:
        topic = topic.strip()
        objective = objective.strip()
        if not topic or not objective:
            raise ValueError("Training topic and objective are required.")
        if scope not in {"global", "project", "agent"}:
            raise ValueError("Training scope must be global, project, or agent.")
        project = self.store.find_project("Ritu Autonomous Company")
        ritu_agent = self.store.find_agent("Ritu")
        scope_id = None
        if scope == "project" and project:
            scope_id = project["id"]
        if scope == "agent" and ritu_agent:
            scope_id = ritu_agent["id"]
        session = self.store.start_training(topic, objective, category, scope, scope_id)
        memories = self.store.relevant_memories(project["id"] if project else None, ritu_agent["id"] if ritu_agent else None, 30)
        reference_context = self.workspace.reference_context(project) if project else ""
        payload = {
            "topic": topic,
            "objective": objective,
            "requested_category": category,
            "scope": scope,
            "source_notes": source_notes[:16000],
            "existing_memory": memories,
            "available_reference_context": reference_context,
        }
        try:
            raw = self.deep_ollama.chat(
                [{"role": "system", "content": TRAINING_SYSTEM}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                json_mode=True,
                temperature=0.15,
                timeout=360,
            )
            learned = self._parse_json(raw)
            if learned.get("needs_input"):
                question = str(learned.get("question") or "What specific outcome should this training improve?")
                summary = str(learned.get("summary") or f"More detail is required for {topic}.")
                training = self.store.finish_training(session["id"], "Needs Input", summary, question)
                return {"ok": True, "training": training, "needs_input": True, "question": question, "summary": summary}

            module_name = str(learned.get("module_name") or topic).strip()
            learned_category = str(learned.get("category") or category).strip()
            module_payload = {
                "name": module_name,
                "category": learned_category,
                "objective": objective,
                "summary": str(learned.get("summary") or ""),
                "knowledge": [str(item) for item in (learned.get("knowledge") or [])],
                "principles": [str(item) for item in (learned.get("principles") or [])],
                "procedures": [str(item) for item in (learned.get("procedures") or [])],
                "guardrails": [str(item) for item in (learned.get("guardrails") or [])],
                "verification_questions": [str(item) for item in (learned.get("verification_questions") or [])],
                "source_notes": source_notes[:16000],
            }
            module_slug = slugify(module_name, "intelligence")
            module_content = self._training_module_content(module_payload)
            if not project:
                raise ValueError("Ritu's self-development project is unavailable.")
            artifact = self.workspace.write_text(
                project,
                f"intelligence/{module_slug}.py",
                module_content,
                summary=f"Training intelligence: {module_name}",
            )
            module = self.store.add_intelligence_module(
                module_name,
                learned_category,
                str(learned.get("summary") or objective),
                artifact["version"],
                artifact["relative_path"],
            )
            created_memories = []
            for memory in (learned.get("memories") or [])[:12]:
                title = str(memory.get("title") or "").strip()
                content = str(memory.get("content") or "").strip()
                if not title or not content:
                    continue
                if self.store.find_matching_memory(scope, scope_id, title, content):
                    continue
                created_memories.append(
                    self.store.add_memory(
                        scope,
                        scope_id,
                        title,
                        content,
                        str(memory.get("reuse_notes") or ""),
                        "Training Room",
                    )
                )
            if not created_memories:
                fallback_content = str(learned.get("summary") or objective).strip()
                fallback_title = module_name
                if not self.store.find_matching_memory(scope, scope_id, fallback_title, fallback_content):
                    created_memories.append(
                        self.store.add_memory(
                            scope,
                            scope_id,
                            fallback_title,
                            fallback_content,
                            "Apply the module's procedures and verification questions when this topic becomes relevant.",
                            "Training Room",
                        )
                    )
            summary = str(learned.get("summary") or f"Ritu learned {module_name}.")
            training = self.store.finish_training(session["id"], "Completed", summary, module_id=module["id"])
            return {
                "ok": True,
                "training": training,
                "module": module,
                "artifact": artifact,
                "memories": created_memories,
                "needs_input": False,
                "summary": summary,
                "training_status": self.training_status(),
            }
        except Exception as error:
            self.store.finish_training(session["id"], "Failed", str(error))
            raise

    @staticmethod
    def _training_module_content(module: dict[str, Any]) -> str:
        return (
            '"""Ritu intelligence module generated from a reviewed Training Room session.\n\n'
            "This module stores declarative operating intelligence and is not executed automatically.\n"
            '"""\n\n'
            f"INTELLIGENCE_MODULE = {pformat(module, width=100, sort_dicts=True)}\n\n"
            "def get_intelligence():\n"
            '    """Return a shallow copy for safe read-only consumption by Ritu and her agents."""\n'
            "    return INTELLIGENCE_MODULE.copy()\n"
        )

    def run_task(self, task_id: str, sleep_after: bool = False) -> dict[str, Any]:
        task = self.store.one("SELECT * FROM tasks WHERE id=?", (task_id,))
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        project = self.store.find_project(task["project_id"])
        agent = self.store.find_agent(task["agent_id"]) if task["agent_id"] else self.store.find_agent("Python Builder")
        if not project or not agent:
            raise ValueError("Task requires a valid project and agent.")
        self.store.set_agent_status(agent["id"], "Active")
        self.store.update_task(task_id, "In Progress")
        memories = self.store.relevant_memories(project["id"], agent["id"])
        context = {
            "project": project,
            "agent": agent,
            "task": task,
            "memories": memories,
            "existing_files": self.workspace.project_file_index(project),
            "references": self.workspace.reference_context(project),
            "acceptance": self._task_acceptance(task),
        }
        messages = [
            {"role": "system", "content": AGENT_SYSTEM},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ]
        raw = self.ollama.chat(messages, json_mode=True, temperature=0.2, timeout=360)
        output = self._parse_json(raw)
        if output.get("needs_input"):
            question = str(output.get("question") or "More information is required.")
            self.store.update_task(task_id, "Blocked", question)
            return {"type": "run_task", "ok": True, "verified": True, "summary": f"{task['title']} is blocked: {question}", "task_id": task_id}

        file_specs = (output.get("files") or [])[:8]
        review = self._quality_review(task, project, agent, file_specs)
        if not review.get("pass"):
            corrected = review.get("corrected_files") if isinstance(review.get("corrected_files"), list) else []
            if corrected:
                file_specs = corrected[:8]
            else:
                summary = str(review.get("summary") or "QA found unresolved acceptance issues.")
                self.store.update_task(task_id, "Review", summary)
                return {"type": "run_task", "ok": True, "verified": True, "summary": summary, "task_id": task_id, "qa": review}
            self.store.add_memory(
                "project",
                project["id"],
                f"QA correction: {task['title']}",
                "; ".join(str(issue) for issue in (review.get("issues") or [])) or "The first deliverable missed acceptance criteria.",
                "Agents must check every explicit task field and value before claiming completion.",
                "QA Agent",
            )

        deterministic_issues = self._deterministic_issues(task, file_specs)
        if deterministic_issues:
            repaired = self._repair_files(task, project, agent, file_specs, deterministic_issues)
            repaired_issues = self._deterministic_issues(task, repaired)
            if repaired_issues:
                summary = "Acceptance checks failed: " + "; ".join(repaired_issues)
                self.store.add_memory(
                    "project",
                    project["id"],
                    f"Acceptance failure: {task['title']}",
                    summary,
                    "Do not mark work complete until deterministic file, symbol, syntax, and literal checks pass.",
                    "Ritu",
                )
                self.store.update_task(task_id, "Review", summary)
                return {
                    "type": "run_task",
                    "ok": True,
                    "verified": True,
                    "summary": summary,
                    "task_id": task_id,
                    "qa": review,
                    "acceptance": {"pass": False, "issues": repaired_issues},
                }
            file_specs = repaired

        written = []
        for file_spec in file_specs:
            path = str(file_spec.get("path") or task.get("deliverable_path") or "").strip()
            content = str(file_spec.get("content") or "")
            if not path or not content:
                continue
            written.append(
                self.workspace.write_text(
                    project,
                    path,
                    content,
                    task_id=task_id,
                    summary=str(file_spec.get("summary") or output.get("summary") or task["title"]),
                )
            )
        for memory in (output.get("memories") or [])[:6]:
            self.store.add_memory(
                "project",
                project["id"],
                str(memory.get("title") or f"Lesson from {task['title']}"),
                str(memory.get("content") or ""),
                str(memory.get("reuse_notes") or ""),
                agent["name"],
            )
        summary = str(output.get("summary") or f"{task['title']} completed.")
        if not written and task.get("deliverable_path"):
            summary += " No file was produced, so the task needs review."
            self.store.update_task(task_id, "Review", summary)
        else:
            self.store.update_task(task_id, "Completed", summary)
        if sleep_after and agent["name"] != "Ritu":
            self.store.set_agent_status(agent["id"], "Sleeping")
        return {
            "type": "run_task",
            "ok": True,
            "verified": True,
            "summary": f"{summary} ({len(written)} files written)",
            "task_id": task_id,
            "files": written,
            "qa": review,
            "acceptance": {"pass": True, "issues": []},
        }

    def _quality_review(
        self,
        task: dict[str, Any],
        project: dict[str, Any],
        agent: dict[str, Any],
        file_specs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        qa_agent = self.store.find_agent("QA Agent")
        if qa_agent:
            self.store.set_agent_status(qa_agent["id"], "Active")
        payload = {
            "project": {"name": project["name"], "objective": project["objective"]},
            "task": {
                "title": task["title"],
                "description": task["description"],
                "deliverable_path": task.get("deliverable_path"),
                "acceptance": self._task_acceptance(task),
            },
            "produced_by": agent["name"],
            "proposed_files": file_specs,
        }
        try:
            raw = self.ollama.chat(
                [{"role": "system", "content": QA_SYSTEM}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                json_mode=True,
                temperature=0.0,
                timeout=300,
            )
            review = self._parse_json(raw)
            if task.get("deliverable_path"):
                paths = [str(item.get("path") or "") for item in file_specs]
                if task["deliverable_path"] not in paths:
                    review["pass"] = False
                    review.setdefault("issues", []).append(f"Required deliverable path missing: {task['deliverable_path']}")
        except Exception as error:
            review = {
                "pass": False,
                "issues": [f"QA review failed: {error}"],
                "summary": "QA could not verify the deliverable, so it remains in review.",
                "corrected_files": [],
            }
        finally:
            if qa_agent:
                self.store.set_agent_status(qa_agent["id"], "Sleeping")
        self.store.add_event(
            "qa_review",
            f"QA {'passed' if review.get('pass') else 'corrected'}: {task['title']}",
            {"task_id": task["id"], "issues": review.get("issues") or []},
        )
        return review

    @staticmethod
    def _task_acceptance(task: dict[str, Any]) -> dict[str, Any]:
        raw = task.get("acceptance") or "{}"
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _deterministic_issues(self, task: dict[str, Any], file_specs: list[dict[str, Any]]) -> list[str]:
        acceptance = self._task_acceptance(task)
        by_path = {str(item.get("path") or ""): str(item.get("content") or "") for item in file_specs}
        required_files = [str(path) for path in acceptance.get("required_files", [])]
        if task.get("deliverable_path") and task["deliverable_path"] not in required_files:
            required_files.append(task["deliverable_path"])
        issues = [f"Missing required file: {path}" for path in required_files if path not in by_path]
        combined = "\n".join(by_path.values())
        for literal in acceptance.get("required_strings", []):
            if str(literal) not in combined:
                issues.append(f"Missing required literal: {literal}")

        python_symbols: set[str] = set()
        function_return_values: dict[str, list[Any]] = {}
        for path, content in by_path.items():
            if not path.lower().endswith(".py"):
                continue
            try:
                tree = ast.parse(content, filename=path)
            except SyntaxError as error:
                issues.append(f"Python syntax error in {path}: {error.msg} at line {error.lineno}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    python_symbols.add(node.name)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    values = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return) and child.value is not None:
                            try:
                                values.append(ast.literal_eval(child.value))
                            except (ValueError, TypeError):
                                continue
                    function_return_values.setdefault(node.name, []).extend(values)
        for symbol in acceptance.get("required_python_symbols", []):
            if str(symbol) not in python_symbols:
                issues.append(f"Missing required Python symbol: {symbol}")
        required_mappings = acceptance.get("required_return_mapping", {})
        if isinstance(required_mappings, dict):
            for function_name, expected in required_mappings.items():
                if not isinstance(expected, dict):
                    continue
                candidates = function_return_values.get(str(function_name), [])
                matched = any(
                    isinstance(candidate, dict)
                    and all(candidate.get(key) == value for key, value in expected.items())
                    for candidate in candidates
                )
                if not matched:
                    issues.append(
                        f"Function {function_name} must return exact mapping values: "
                        + json.dumps(expected, ensure_ascii=False, sort_keys=True)
                    )
        return issues

    def _repair_files(
        self,
        task: dict[str, Any],
        project: dict[str, Any],
        agent: dict[str, Any],
        file_specs: list[dict[str, Any]],
        issues: list[str],
    ) -> list[dict[str, Any]]:
        payload = {
            "project": {"name": project["name"], "objective": project["objective"]},
            "task": {
                "title": task["title"],
                "description": task["description"],
                "deliverable_path": task.get("deliverable_path"),
                "acceptance": self._task_acceptance(task),
            },
            "produced_by": agent["name"],
            "deterministic_failures": issues,
            "files_to_correct": file_specs,
        }
        raw = self.ollama.chat(
            [
                {
                    "role": "system",
                    "content": (
                        QA_SYSTEM
                        + "\nMachine checks failed. Correct every listed failure exactly. "
                        "Return complete corrected_files; do not merely explain."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            json_mode=True,
            temperature=0.0,
            timeout=300,
        )
        result = self._parse_json(raw)
        corrected = result.get("corrected_files")
        return corrected[:8] if isinstance(corrected, list) else []

    def _execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        action_type = str(action.get("type") or "")
        args = action.get("args") if isinstance(action.get("args"), dict) else {}
        if action_type == "create_project":
            name = str(args.get("name") or "").strip()
            objective = str(args.get("objective") or "").strip()
            if not name or not objective:
                raise ValueError("Project name and objective are required.")
            project = self.store.create_project(name, slugify(name), objective, str(args.get("phase") or "Discovery"))
            metadata = {
                key: args[key]
                for key in ("priority", "progress", "health", "milestone", "blocker", "owner")
                if args.get(key) is not None
            }
            if metadata:
                project = self.store.update_project(project["id"], metadata)
            self.workspace.initialize_project(project)
            return {"type": action_type, "ok": True, "verified": True, "summary": f"created project {project['name']}", "project_id": project["id"], "record": project}

        if action_type == "update_project":
            reference = str(args.get("project") or "").strip()
            updates = {
                "objective": args.get("description") if args.get("description") is not None else args.get("objective"),
                "status": args.get("status"),
                "phase": args.get("phase"),
                "priority": args.get("priority"),
                "progress": args.get("progress"),
                "health": args.get("health"),
                "milestone": args.get("milestone"),
                "blocker": args.get("blocker"),
                "owner": args.get("owner"),
            }
            updated = self.store.update_project(reference, updates)
            return {
                "type": action_type,
                "ok": True,
                "verified": True,
                "summary": f"updated project {updated['name']}",
                "project_id": updated["id"],
                "record": updated,
            }

        if action_type == "hire_agent":
            project = self.store.find_project(str(args.get("project") or "") or None)
            agent = self.store.create_agent(
                str(args.get("name") or "").strip(),
                str(args.get("role") or "").strip(),
                [str(item) for item in (args.get("capabilities") or [])],
                project["id"] if project else None,
                str(args.get("status") or "Active"),
                "Capture issues, fixes, outcomes, and reusable patterns.",
            )
            return {"type": action_type, "ok": True, "verified": True, "summary": f"hired {agent['name']}", "agent_id": agent["id"], "record": agent}

        if action_type == "update_agent":
            reference = str(args.get("agent") or "").strip()
            project = self.store.find_project(str(args.get("project") or "")) if args.get("project") else None
            updates = {
                "role": args.get("role"),
                "capabilities": args.get("capabilities") if isinstance(args.get("capabilities"), list) else None,
                "status": args.get("status"),
                "project_id": project["id"] if project else None,
                "progress": args.get("progress"),
                "signal": args.get("signal"),
                "dependencies": args.get("dependencies"),
                "last_update": args.get("last_update"),
                "memory_policy": args.get("memory_policy"),
            }
            updated = self.store.update_agent(reference, updates)
            return {
                "type": action_type,
                "ok": True,
                "verified": True,
                "summary": f"updated agent {updated['name']}",
                "agent_id": updated["id"],
                "record": updated,
            }

        if action_type in {"sleep_agent", "wake_agent", "archive_agent"}:
            statuses = {"sleep_agent": "Sleeping", "wake_agent": "Active", "archive_agent": "Archived"}
            agent = self.store.set_agent_status(str(args.get("agent") or ""), statuses[action_type])
            return {"type": action_type, "ok": True, "verified": True, "summary": f"{agent['name']} is {agent['status']}", "agent_id": agent["id"], "record": agent}

        if action_type == "create_task":
            project = self.store.find_project(str(args.get("project") or "") or None)
            if not project:
                raise ValueError("No active project is available.")
            agent = self.store.find_agent(str(args.get("agent") or "")) if args.get("agent") else None
            task = self.store.create_task(
                project["id"],
                str(args.get("title") or "").strip(),
                str(args.get("description") or "").strip(),
                agent["id"] if agent else None,
                str(args.get("priority") or "Medium"),
                str(args.get("deliverable_path") or "") or None,
                args.get("acceptance") if isinstance(args.get("acceptance"), dict) else {},
            )
            if args.get("auto_run"):
                return self.run_task(task["id"], sleep_after=bool(args.get("sleep_after")))
            return {"type": action_type, "ok": True, "verified": True, "summary": f"assigned task {task['title']}", "task_id": task["id"], "record": task}

        if action_type == "update_task":
            agent = self.store.find_agent(str(args.get("agent") or "")) if args.get("agent") else None
            updates = {
                "title": args.get("title"),
                "description": args.get("description"),
                "status": args.get("status"),
                "priority": args.get("priority"),
                "agent_id": agent["id"] if agent else None,
                "deliverable_path": args.get("deliverable_path"),
                "result": args.get("result"),
            }
            updated = self.store.update_task_record(str(args.get("task") or ""), updates)
            return {
                "type": action_type,
                "ok": True,
                "verified": True,
                "summary": f"updated task {updated['title']}",
                "task_id": updated["id"],
                "record": updated,
            }

        if action_type == "run_task":
            return self.run_task(str(args.get("task_id") or ""), sleep_after=bool(args.get("sleep_after")))

        if action_type == "write_file":
            scope = str(args.get("scope") or "project")
            project = self.store.find_project(str(args.get("project") or "") or None)
            if scope == "project" and not project:
                raise ValueError("No active project is available.")
            result = self.workspace.write_scoped_text(
                scope,
                str(args.get("path") or ""),
                str(args.get("content") or ""),
                project,
                summary=str(args.get("summary") or "Written by Ritu"),
            )
            return {
                "type": action_type,
                "ok": True,
                "verified": True,
                "summary": f"wrote and verified {result['path']}",
                "file": result,
            }

        if action_type == "patch_file":
            scope = str(args.get("scope") or "project")
            project = self.store.find_project(str(args.get("project") or "") or None)
            if scope == "project" and not project:
                raise ValueError("No active project is available.")
            result = self.workspace.patch_scoped_text(
                scope,
                str(args.get("path") or ""),
                str(args.get("find") or ""),
                str(args.get("replace") or ""),
                project,
                summary=str(args.get("summary") or "Patched by Ritu"),
            )
            return {
                "type": action_type,
                "ok": True,
                "verified": True,
                "summary": f"patched and verified {result['path']}",
                "file": result,
            }

        if action_type == "add_memory":
            scope = str(args.get("scope") or "global")
            if scope not in {"global", "project", "agent"}:
                raise ValueError("Memory scope must be global, project, or agent.")
            memory = self.store.add_memory(
                scope,
                str(args.get("scope_id") or "") or None,
                str(args.get("title") or "").strip(),
                str(args.get("content") or "").strip(),
                str(args.get("reuse_notes") or ""),
            )
            return {"type": action_type, "ok": True, "summary": f"captured memory {memory['title']}", "memory_id": memory["id"]}

        if action_type == "train_ritu":
            result = self.train(
                str(args.get("topic") or ""),
                str(args.get("objective") or ""),
                str(args.get("category") or "Operations"),
                str(args.get("scope") or "global"),
                str(args.get("source_notes") or ""),
            )
            summary = str(result.get("summary") or result.get("training", {}).get("summary") or "training captured")
            return {
                "type": action_type,
                "ok": True,
                "summary": summary,
                "training": result.get("training"),
                "module": result.get("module"),
                "needs_input": bool(result.get("needs_input")),
                "question": result.get("question", ""),
            }

        raise ValueError(f"Unsupported autonomous action: {action_type}")

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Model did not return a valid action plan.")
            parsed = json.loads(raw[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("Model action plan must be a JSON object.")
        return parsed
