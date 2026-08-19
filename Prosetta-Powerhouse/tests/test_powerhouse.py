from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from powerhouse.config import confined_path, slugify
from powerhouse.orchestrator import RituOrchestrator
from powerhouse.store import CompanyStore
from powerhouse.workspace import PowerhouseWorkspace


class PowerhouseCoreTests(unittest.TestCase):
    def test_confined_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                confined_path(root, "../outside.py")

    def test_slugify_is_stable(self) -> None:
        self.assertEqual(slugify(" Ritu Autonomous Company "), "ritu-autonomous-company")

    def test_agent_lifecycle_and_versioned_file_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = CompanyStore(root / "company.db")
            project = store.create_project("Test Project", "test-project", "Validate local execution")
            agent = store.create_agent("Builder", "Python builder", ["python"], project["id"], "Active")
            self.assertEqual(store.set_agent_status(agent["id"], "Sleeping")["status"], "Sleeping")

            with patch("powerhouse.workspace.PROJECTS_ROOT", root / "projects"):
                workspace = PowerhouseWorkspace(store)
                first = workspace.write_text(project, "src/example.py", "VALUE = 1\n")
                second = workspace.write_text(project, "src/example.py", "VALUE = 2\n")
                self.assertEqual(first["version"], 1)
                self.assertEqual(second["version"], 2)
                self.assertEqual(Path(second["path"]).read_text(encoding="utf-8"), "VALUE = 2\n")
                history = list((root / "projects" / "test-project" / ".history").rglob("*.bak"))
                self.assertEqual(len(history), 1)
                with self.assertRaises(ValueError):
                    workspace.write_text(project, "unsafe.exe", "not allowed")

    def test_scoped_file_api_reads_writes_patches_and_blocks_internal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            portal_root = root / "portal"
            projects_root = root / "projects"
            ritu_root = root / "powerhouse"
            portal_root.mkdir()
            (ritu_root / ".ritu").mkdir(parents=True)
            store = CompanyStore(ritu_root / ".ritu" / "company.db")
            project = store.create_project("File API", "file-api", "Verify local workspace access")
            with (
                patch("powerhouse.workspace.REPO_ROOT", portal_root),
                patch("powerhouse.workspace.PROJECTS_ROOT", projects_root),
                patch("powerhouse.workspace.RITU_ROOT", ritu_root),
            ):
                workspace = PowerhouseWorkspace(store)
                created = workspace.write_scoped_text("project", "src/worker.py", "VALUE = 1\n", project)
                self.assertTrue(created["verified"])
                self.assertEqual(workspace.read_text_file("project", "src/worker.py", project)["content"], "VALUE = 1\n")
                patched = workspace.patch_scoped_text(
                    "project",
                    "src/worker.py",
                    "VALUE = 1",
                    "VALUE = 2",
                    project,
                )
                self.assertEqual(patched["content"], "VALUE = 2\n")

                portal = workspace.write_scoped_text("portal", "connected.js", "const CONNECTED = true;\n")
                self.assertTrue(portal["verified"])
                self.assertIn("connected.js", [item["path"] for item in workspace.list_files("portal")])
                with self.assertRaises(ValueError):
                    workspace.write_scoped_text("portal", ".env", "SECRET=value")
                with self.assertRaises(ValueError):
                    workspace.write_scoped_text("project", ".history/private.py", "VALUE = 3\n", project)

    def test_machine_acceptance_checks_python_contract(self) -> None:
        orchestrator = object.__new__(RituOrchestrator)
        task = {
            "deliverable_path": "src/readiness_probe.py",
            "acceptance": (
                '{"required_files":["src/readiness_probe.py"],'
                '"required_strings":["Ritu eCEO","local Powerhouse"],'
                '"required_python_symbols":["report"],'
                '"required_return_mapping":{"report":{"service":"Ritu eCEO","status":"ready","workspace":"local Powerhouse"}}}'
            ),
        }
        bad = [{"path": "src/readiness_probe.py", "content": "def report():\n    return {'status': 'ready'}\n"}]
        issues = orchestrator._deterministic_issues(task, bad)
        self.assertIn("Missing required literal: Ritu eCEO", issues)
        self.assertIn("Missing required literal: local Powerhouse", issues)
        self.assertTrue(any("must return exact mapping values" in issue for issue in issues))

        good = [
            {
                "path": "src/readiness_probe.py",
                "content": (
                    "def report():\n"
                    "    return {'service': 'Ritu eCEO', 'status': 'ready', "
                    "'workspace': 'local Powerhouse'}\n"
                ),
            }
        ]
        self.assertEqual(orchestrator._deterministic_issues(task, good), [])

    def test_training_session_and_intelligence_module_are_persistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CompanyStore(Path(directory) / "company.db")
            session = store.start_training(
                "Decision quality",
                "Teach Ritu to verify assumptions before delegation.",
                "Leadership",
                "global",
                None,
            )
            module = store.add_intelligence_module(
                "Decision Quality",
                "Leadership",
                "A reusable decision-checking procedure.",
                1,
                "intelligence/decision-quality.py",
            )
            completed = store.finish_training(
                session["id"],
                "Completed",
                "Ritu learned a decision verification loop.",
                module_id=module["id"],
            )
            status = store.training_status()
            self.assertEqual(completed["module_id"], module["id"])
            self.assertEqual(status["counts"]["sessions"], 1)
            self.assertEqual(status["counts"]["completed"], 1)
            self.assertEqual(status["counts"]["modules"], 1)

    def test_training_module_is_valid_declarative_python(self) -> None:
        content = RituOrchestrator._training_module_content(
            {
                "name": "Reusable Learning Loop",
                "category": "Memory",
                "principles": ["Capture the root cause and validation result."],
            }
        )
        compile(content, "intelligence/reusable-learning-loop.py", "exec")
        self.assertIn("INTELLIGENCE_MODULE", content)
        self.assertIn("def get_intelligence", content)
        self.assertIn("not executed automatically", content)

    def test_matching_memory_prevents_training_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CompanyStore(Path(directory) / "company.db")
            original = store.add_memory(
                "global",
                None,
                "Learning Standard",
                "Capture the issue, root cause, change, result, and reuse guidance.",
            )
            matched = store.find_matching_memory(
                "global",
                None,
                "learning standard",
                "Different wording is intentionally ignored because the title matches.",
            )
            self.assertEqual(matched["id"], original["id"])

    def test_training_chat_requires_explicit_permission_before_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            orchestrator = object.__new__(RituOrchestrator)
            orchestrator.store = CompanyStore(Path(directory) / "company.db")
            orchestrator.fast_ollama = Mock(model="qwen2.5:7b")
            orchestrator.deep_ollama = Mock(model="qwen2.5:14b")
            orchestrator.ollama = orchestrator.fast_ollama
            orchestrator.workspace = PowerhouseWorkspace(orchestrator.store)
            orchestrator.deep_ollama.chat.return_value = (
                '{"response":"I propose adding a status-review capability.",'
                '"needs_input":false,'
                '"actions":[{"type":"train_ritu","args":{"topic":"Status Review",'
                '"objective":"Learn a repeatable status review.","category":"Operations",'
                '"scope":"global","source_notes":""}}]}'
            )
            result = orchestrator.chat(
                "Let us discuss a status-review capability.",
                "training-test",
                {},
                "training",
            )
            self.assertTrue(result["needs_input"])
            self.assertEqual(result["actions"], [])
            self.assertIn("No training change has been applied", result["response"])
            self.assertEqual(orchestrator.store.training_status()["counts"]["sessions"], 0)

    def test_room_model_routing_uses_deep_only_for_training_and_boardroom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            orchestrator = object.__new__(RituOrchestrator)
            orchestrator.store = CompanyStore(Path(directory) / "company.db")
            orchestrator.fast_ollama = Mock(model="qwen2.5:7b")
            orchestrator.deep_ollama = Mock(model="qwen2.5:14b")
            orchestrator.ollama = orchestrator.fast_ollama
            orchestrator.workspace = PowerhouseWorkspace(orchestrator.store)
            answer = '{"response":"Status verified.","needs_input":false,"actions":[]}'
            orchestrator.fast_ollama.chat.return_value = answer
            orchestrator.deep_ollama.chat.return_value = answer

            command = orchestrator.chat("Give me company status.", "fast-route", {}, "company")
            boardroom = orchestrator.chat("Review this strategic decision.", "deep-route", {}, "boardroom")

            self.assertEqual(command["model"], "qwen2.5:7b")
            self.assertEqual(boardroom["model"], "qwen2.5:14b")
            orchestrator.fast_ollama.chat.assert_called_once()
            orchestrator.deep_ollama.chat.assert_called_once()

    def test_portal_state_is_authoritative_and_updates_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CompanyStore(Path(directory) / "company.db")
            project = store.create_project("Live Portal", "live-portal", "Initial description")
            agent = store.create_agent("Nova", "Researcher", ["research"], project["id"], "Sleeping")
            task = store.create_task(project["id"], "Validate source", "Verify live facts", agent["id"])

            updated_project = store.update_project(
                project["id"],
                {"objective": "Updated by Boardroom", "progress": 35, "milestone": "Approval"},
            )
            updated_agent = store.update_agent(
                agent["id"],
                {"status": "Active", "progress": 20, "signal": "Strong", "capabilities": ["research", "verification"]},
            )
            updated_task = store.update_task_record(task["id"], {"status": "In Progress", "priority": "High"})
            portal = store.portal_state()

            self.assertEqual(updated_project["objective"], "Updated by Boardroom")
            self.assertEqual(updated_agent["status"], "Active")
            self.assertEqual(updated_task["status"], "In Progress")
            self.assertEqual(portal["projects"][0]["description"], "Updated by Boardroom")
            self.assertEqual(portal["agents"][0]["capabilities"], ["research", "verification"])
            self.assertEqual(portal["tasks"][0]["project"], project["id"])
            self.assertGreater(portal["revision"], 0)
            self.assertTrue(portal["verified_at"])


if __name__ == "__main__":
    unittest.main()
