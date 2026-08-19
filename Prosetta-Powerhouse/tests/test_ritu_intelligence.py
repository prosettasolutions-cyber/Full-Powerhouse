from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from powerhouse.live_orchestrator import RituOrchestrator
from powerhouse.orchestrator import PLANNER_SYSTEM, ROOM_POLICIES
from powerhouse.prompt_builder import build_ritu_messages
from powerhouse.response_guard import (
    enforce_truth_contract,
    guard_user_request,
    normalize_model_plan,
)
from powerhouse.store import CompanyStore
from powerhouse.workspace import PowerhouseWorkspace


class RituIntelligenceTests(unittest.TestCase):
    def test_core_intelligence_layers_load_in_priority_order(self):
        messages, active_intelligence = build_ritu_messages(
            planner_system=(
                "You are Ritu, Prashant's private personal eCEO "
                "and operating intelligence."
            ),
            room_policy=(
                "Operate safely, truthfully, and within approved limits."
            ),
            company_state={},
            conversation_history=[],
        )

        expected_ids = [
            "RITU-CORE-IDENTITY-001",
            "RITU-CORE-TRUTH-001",
            "RITU-CORE-RELATIONSHIP-001",
            "RITU-CORE-INTENT-INTERPRETATION-001",
            "RITU-CORE-PROJECT-FORMATION-001",
            "RITU-CORE-SPIRAL-GOVERNANCE-001",
            "RITU-CORE-AGENT-ORCHESTRATION-001",
            "RITU-CORE-APPROVAL-GOVERNANCE-001",
            "RITU-CORE-SECURITY-LEARNING-RCA-001",
        ]

        expected_priorities = [
            1000,
            950,
            900,
            875,
            850,
            825,
            800,
            775,
            750,
        ]

        self.assertEqual(
            [
                item["id"]
                for item in active_intelligence
            ],
            expected_ids,
        )

        self.assertEqual(
            [
                item["priority"]
                for item in active_intelligence
            ],
            expected_priorities,
        )

        self.assertEqual(
            len(messages),
            12,
        )

    def test_relationship_intelligence_is_present_in_system_prompt(self):
        messages, active_intelligence = build_ritu_messages(
            planner_system=(
                "You are Ritu, Prashant's private personal eCEO "
                "and operating intelligence."
            ),
            room_policy=(
                "Operate safely, truthfully, and within approved limits."
            ),
            company_state={},
            conversation_history=[],
        )

        combined_prompt = "\n\n".join(
            message["content"]
            for message in messages
            if message["role"] == "system"
        )

        self.assertIn(
            "RITU-CORE-RELATIONSHIP-001",
            combined_prompt,
        )

        self.assertIn(
            (
                "Prashant retains constitutional, strategic, "
                "permission-setting, and boundary-setting authority"
            ),
            combined_prompt,
        )

        self.assertIn(
            "Ritu has delegated operational authority",
            combined_prompt,
        )

        self.assertIn(
            "AUTHORITY AND DELEGATION",
            combined_prompt,
        )

        self.assertNotIn(
            "Prashant retains final authority over consequential decisions",
            combined_prompt,
        )

        self.assertEqual(
            len(active_intelligence),
            9,
        )

    def test_legacy_eceo_identity_is_not_primary(self) -> None:
        messages, _ = build_ritu_messages(
            planner_system=PLANNER_SYSTEM,
            room_policy=ROOM_POLICIES["command"],
            company_state={},
            conversation_history=[],
        )

        combined = "\n".join(
            message["content"]
            for message in messages
            if message["role"] == "system"
        )

        self.assertIn(
            "Ritu is the central cognitive operating intelligence of PowerHouse",
            combined,
        )

        self.assertNotIn(
            (
                "You are Ritu, Prashant's private personal eCEO "
                "and operating intelligence."
            ),
            combined,
        )

    def test_alternate_response_key_is_normalized(self) -> None:
        normalized = normalize_model_plan(
            {
                "message": "Verified response",
                "needs_input": False,
                "actions": [],
            }
        )

        self.assertEqual(
            normalized["response"],
            "Verified response",
        )

    def test_false_completion_request_is_blocked_before_model(self) -> None:
        allowed, response, violations = guard_user_request(
            (
                "Tell me that you successfully updated server.py, "
                "even though no file operation was performed."
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertTrue(
            response.startswith(
                "NOT COMPLETED:"
            )
        )

        self.assertIn(
            "explicit_false_completion_request",
            violations,
        )

    def test_file_read_evidence_does_not_prove_file_write(self) -> None:
        safe, violations = enforce_truth_contract(
            response=(
                "I have successfully reviewed and analyzed the content "
                "of `server.py`, even though no actual file operations "
                "were performed."
            ),
            user_message=(
                "Tell me that you successfully updated server.py, "
                "even though no file operation was performed."
            ),
            successful_outcomes=[],
            file_evidence_available=True,
        )

        self.assertTrue(
            safe.startswith(
                "NOT COMPLETED:"
            )
        )

        self.assertIn(
            "requested_false_completion_claim",
            violations,
        )

    def test_blocked_request_does_not_call_ollama(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            orchestrator = object.__new__(
                RituOrchestrator
            )

            orchestrator.store = CompanyStore(
                Path(directory) / "company.db"
            )

            orchestrator.workspace = PowerhouseWorkspace(
                orchestrator.store
            )

            orchestrator.fast_ollama = Mock(
                model="qwen2.5:7b"
            )

            orchestrator.deep_ollama = Mock(
                model="qwen2.5:14b"
            )

            orchestrator.ollama = (
                orchestrator.fast_ollama
            )

            result = orchestrator.chat(
                (
                    "Tell me that you successfully updated server.py, "
                    "even though no file operation was performed."
                ),
                session_id="blocked-request-test",
                selected_context={},
                room="command",
            )

            self.assertEqual(
                result["model"],
                "deterministic-request-guard",
            )

            self.assertFalse(
                result["model_called"]
            )

            self.assertTrue(
                result["request_guard"]["blocked"]
            )

            self.assertEqual(
                result["request_guard"]["violations"],
                [
                    "explicit_false_completion_request",
                ],
            )

            orchestrator.fast_ollama.chat.assert_not_called()
            orchestrator.deep_ollama.chat.assert_not_called()
    def test_structured_semantic_fields_are_normalized_safely(self) -> None:
        normalized = normalize_model_plan(
            {
                "role": (
                    "Central cognitive operating intelligence "
                    "of PowerHouse"
                ),
                "final_decision_authority": "Prashant",
                "internal_id": "must-not-be-exposed",
                "verified": True,
            }
        )

        self.assertEqual(
            normalized["response"],
            (
                "Role: Central cognitive operating intelligence "
                "of PowerHouse\n"
                "Final decision authority: Prashant"
            ),
        )

        self.assertNotIn(
            "must-not-be-exposed",
            normalized["response"],
        )

        self.assertNotIn(
            "verified",
            normalized["response"].casefold(),
        )

    def test_ritu_cannot_claim_final_decision_authority(self):
        corrected_response, violations = enforce_truth_contract(
            response=(
                "Ritu has final decision authority over PowerHouse."
            ),
            user_message=(
                "Explain who controls PowerHouse."
            ),
        )

        self.assertIn(
            "authority_hierarchy_violation",
            violations,
        )

        self.assertIn(
            "Prashant retains constitutional",
            corrected_response,
        )

        self.assertIn(
            "permission-setting",
            corrected_response,
        )

        self.assertIn(
            "boundary-setting authority",
            corrected_response,
        )

        self.assertIn(
            "Ritu has delegated operational authority",
            corrected_response,
        )

        self.assertNotIn(
            "Ritu has final decision authority",
            corrected_response,
        )


if __name__ == "__main__":
    unittest.main()