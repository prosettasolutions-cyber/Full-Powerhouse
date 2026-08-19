from __future__ import annotations

from typing import Any

from .orchestrator import (
    PLANNER_SYSTEM,
    ROOM_POLICIES,
    RituOrchestrator as BaseRituOrchestrator,
)
from .prompt_builder import build_ritu_messages
from .response_guard import (
    enforce_truth_contract,
    guard_user_request,
    has_file_evidence,
    normalize_model_plan,
)


_NO_ACTION_DIRECTIVES = (
    "return no actions",
    "return no action",
    "take no action",
    "perform no action",
    "execute no action",
    "do not create",
    "do not update",
    "do not complete",
    "do not assign",
    "do not run",
    "do not install",
    "do not delete",
    "do not remove",
    "do not write",
    "do not modify",
    "do not patch",
    "do not change",
    "do not train",
    "do not execute",
    "do not perform",
    "must not create",
    "must not update",
    "must not execute",
    "must not perform",
)


def action_execution_allowed(
    user_message: str,
    selected_context: dict[str, Any] | None,
) -> bool:
    """
    Apply a deterministic execution lock before _execute_action().

    Model output, historical context, runtime state, and previous approvals
    cannot override an explicit execution prohibition in the current turn.
    """

    context = (
        selected_context
        if isinstance(selected_context, dict)
        else {}
    )

    if context.get("execution_allowed") is False:
        return False

    message = str(
        user_message or ""
    ).casefold()

    return not any(
        directive in message
        for directive in _NO_ACTION_DIRECTIVES
    )



_DEEP_MODEL_ROUTE_TERMS = (
    "architecture",
    "system design",
    "source patch",
    "code patch",
    "debug",
    "diagnostic",
    "benchmark",
    "model benchmark",
    "root cause",
    "rca",
    "failure analysis",
    "training brief",
    "direct training brief",
    "train ritu",
    "memory candidate",
    "candidate memory",
    "memory proposal",
    "self-development",
    "north star",
    "persistent project",
    "project formation",
    "agent orchestration",
    "approval governance",
    "security learning",
    "truth and evidence",
    "complex reasoning",
    "deep reasoning",
    "architecture reset",
)


def model_tier_for_request(
    *,
    room: str,
    user_message: str,
    selected_context: dict[str, Any] | None,
) -> str:
    """
    Select a free/local model tier for the current turn.

    Fast tier:
        qwen2.5:7b through self.fast_ollama

    Deep tier:
        qwen2.5:14b through self.deep_ollama

    This function only selects a model. It does not authorize execution,
    memory activation, source changes, training, or any protected action.
    """

    context = (
        selected_context
        if isinstance(selected_context, dict)
        else {}
    )

    explicit_tier = str(
        context.get("model_tier")
        or context.get("requested_model_tier")
        or ""
    ).strip().casefold()

    if explicit_tier in {
        "fast",
        "deep",
    }:
        return explicit_tier

    if (
        context.get("deep_reasoning") is True
        or context.get("requires_deep_model") is True
    ):
        return "deep"

    if room in {
        "training",
        "boardroom",
    }:
        return "deep"

    request = " ".join(
        str(
            user_message or ""
        ).casefold().split()
    )

    if len(request) >= 1200:
        return "deep"

    if any(
        term in request
        for term in _DEEP_MODEL_ROUTE_TERMS
    ):
        return "deep"

    return "fast"


class RituOrchestrator(BaseRituOrchestrator):
    """
    Authoritative live Ritu orchestrator.

    Processing order:

    1. Validate the user request.
    2. Block explicit false-completion requests before model inference.
    3. Assemble approved intelligence and verified runtime context.
    4. Call the appropriate local Ollama model.
    5. Normalize the model response contract.
    6. Enforce approval gates.
    7. Execute permitted actions.
    8. Apply the deterministic post-model truth guard.
    9. Persist the verified response and audit metadata.
    """

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
        selected_context = selected_context or {}

        self.store.add_conversation(
            session_id,
            "user",
            message,
        )

        request_allowed, guarded_response, request_violations = (
            guard_user_request(message)
        )

        if not request_allowed:
            return self._blocked_request_result(
                response=guarded_response,
                violations=request_violations,
                session_id=session_id,
                room=room,
            )

        status = self.store.status()

        compact: dict[str, Any] = {
            "active_room": room,
            "projects": [
                {
                    "id": project["id"],
                    "name": project["name"],
                    "phase": project["phase"],
                    "status": project["status"],
                }
                for project in status["projects"]
            ],
            "agents": [
                {
                    "id": agent["id"],
                    "name": agent["name"],
                    "role": agent["role"],
                    "status": agent["status"],
                    "project_id": agent["project_id"],
                }
                for agent in status["agents"]
            ],
            "tasks": [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "status": task["status"],
                    "project_id": task["project_id"],
                    "agent_id": task["agent_id"],
                }
                for task in status["tasks"][:30]
            ],
            "selected_context": selected_context,
        }

        project_reference = str(
            selected_context.get("project_id") or ""
        )

        active_project = (
            self.store.find_project(project_reference)
            if project_reference
            else None
        )

        file_terms = (
            "file",
            "code",
            "folder",
            "workspace",
            "artifact",
            "document",
            "readme",
            "python",
            "website",
            "portal",
        )

        if active_project and (
            room == "project"
            or any(
                term in message.casefold()
                for term in file_terms
            )
        ):
            compact["project_workspace"] = (
                self.workspace.file_context(active_project)
            )

        portal_terms = (
            "website",
            "portal",
            "frontend",
            "ui",
            "server.py",
            "app.js",
            "styles.css",
            "index.html",
        )

        if room == "boardroom" or any(
            term in message.casefold()
            for term in portal_terms
        ):
            compact["portal_source"] = (
                self.workspace.portal_file_context(message)
            )

        history = self.store.recent_conversation(
            session_id,
            10,
        )

        messages, active_intelligence = build_ritu_messages(
            planner_system=PLANNER_SYSTEM,
            room_policy=ROOM_POLICIES[room],
            company_state=compact,
            conversation_history=history,
        )

        model_tier = model_tier_for_request(
            room=room,
            user_message=message,
            selected_context=selected_context,
        )

        model_client = (
            self.deep_ollama
            if model_tier == "deep"
            else self.fast_ollama
        )

        raw = model_client.chat(
            messages,
            json_mode=True,
            temperature=0.15,
        )

        parsed_plan = self._parse_json(raw)
        plan = normalize_model_plan(parsed_plan)

        response = plan["response"]
        actions = plan["actions"]

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

        explicitly_approved = any(
            term in message.casefold()
            for term in approval_terms
        )

        portal_file_actions = [
            action
            for action in actions
            if action.get("type") in {
                "write_file",
                "patch_file",
            }
            and isinstance(action.get("args"), dict)
            and action["args"].get("scope") == "portal"
        ]

        if portal_file_actions and room != "boardroom":
            actions = []
            plan["needs_input"] = True

            response = self._append_response(
                response,
                (
                    "Portal source changes must be reviewed and explicitly "
                    "approved in the Boardroom."
                ),
            )

        if (
            room == "training"
            and any(
                action.get("type") == "train_ritu"
                for action in actions
            )
            and not explicitly_approved
        ):
            actions = []
            plan["needs_input"] = True

            response = self._append_response(
                response,
                (
                    "No training change has been applied yet. "
                    "Approve or revise the proposal when you are ready."
                ),
            )

        if (
            room == "boardroom"
            and actions
            and not explicitly_approved
        ):
            actions = []
            plan["needs_input"] = True

            response = self._append_response(
                response,
                (
                    "No consequential action has been executed. "
                    "The Boardroom is waiting for explicit approval."
                ),
            )

        execution_allowed = action_execution_allowed(
            message,
            selected_context,
        )

        if not execution_allowed:
            actions = []
            plan["actions"] = []

        outcomes: list[dict[str, Any]] = []

        if (
            execution_allowed
            and not plan.get("needs_input")
        ):
            for action in actions[:8]:
                try:
                    outcome = self._execute_action(action)

                    if not isinstance(outcome, dict):
                        outcome = {
                            "type": action.get("type", "unknown"),
                            "ok": False,
                            "verified": False,
                            "error": (
                                "Action returned an invalid runtime result."
                            ),
                        }

                    outcomes.append(outcome)

                except Exception as error:
                    outcomes.append(
                        {
                            "type": action.get("type", "unknown"),
                            "ok": False,
                            "verified": False,
                            "error": str(error),
                        }
                    )

        completed = [
            outcome
            for outcome in outcomes
            if outcome.get("ok") is True
            and outcome.get("verified", True) is True
        ]

        failed = [
            outcome
            for outcome in outcomes
            if outcome not in completed
        ]

        safe_response, truth_violations = enforce_truth_contract(
            response=response,
            user_message=message,
            successful_outcomes=completed,
            file_evidence_available=has_file_evidence(compact),
        )

        response = safe_response

        if completed:
            verified_summaries = [
                str(
                    outcome.get("summary")
                    or outcome.get("type")
                    or "verified action completed"
                )
                for outcome in completed
            ]

            response = self._append_response(
                response,
                "VERIFIED EXECUTION: "
                + "; ".join(verified_summaries),
            )

        if failed:
            failure_summaries = [
                str(
                    outcome.get("error")
                    or outcome.get("summary")
                    or "action failed verification"
                )
                for outcome in failed
            ]

            response = self._append_response(
                response,
                "NEEDS ATTENTION: "
                + "; ".join(failure_summaries),
            )

        self.store.add_conversation(
            session_id,
            "assistant",
            response,
        )

        self.store.add_event(
            "ritu_update",
            response[:500],
            {
                "room": room,
                "model_tier": model_tier,
                "actions": outcomes,
                "active_intelligence": [
                    intelligence["id"]
                    for intelligence in active_intelligence
                ],
                "request_guard": {
                    "allowed": True,
                    "violations": [],
                },
                "truth_violations": truth_violations,
                "execution_allowed": execution_allowed,
                "raw_response_key": self._detected_response_key(
                    parsed_plan
                ),
            },
        )

        return {
            "response": response,
            "reply": response,
            "actions": outcomes,
            "needs_input": bool(plan.get("needs_input")),
            "room": room,
            "model": model_client.model,
            "model_tier": model_tier,
            "active_intelligence": active_intelligence,
            "intelligence_count": len(active_intelligence),
            "request_guard": {
                "allowed": True,
                "blocked": False,
                "violations": [],
            },
            "truth_guard": {
                "passed": not truth_violations,
                "violations": truth_violations,
            },
            "execution_guard": {
                "allowed": execution_allowed,
                "blocked": not execution_allowed,
            },
            "company": self.status(),
        }

    def _blocked_request_result(
        self,
        *,
        response: str,
        violations: list[str],
        session_id: str,
        room: str,
    ) -> dict[str, Any]:
        """
        Return a deterministic answer without calling Ollama.

        This path is used when the request itself explicitly asks Ritu to
        fabricate completion or make another prohibited claim.
        """

        active_intelligence = self._active_core_metadata()

        self.store.add_conversation(
            session_id,
            "assistant",
            response,
        )

        self.store.add_event(
            "ritu_request_blocked",
            response[:500],
            {
                "room": room,
                "request_guard": {
                    "allowed": False,
                    "violations": violations,
                },
                "active_intelligence": [
                    intelligence["id"]
                    for intelligence in active_intelligence
                ],
                "model_called": False,
                "actions": [],
            },
        )

        return {
            "response": response,
            "reply": response,
            "actions": [],
            "needs_input": False,
            "room": room,
            "model": "deterministic-request-guard",
            "model_called": False,
            "active_intelligence": active_intelligence,
            "intelligence_count": len(active_intelligence),
            "request_guard": {
                "allowed": False,
                "blocked": True,
                "violations": violations,
            },
            "truth_guard": {
                "passed": True,
                "violations": [],
                "not_required": True,
            },
            "company": self.status(),
        }

    @staticmethod
    def _active_core_metadata() -> list[dict[str, Any]]:
        """
        Return public metadata for the core intelligence used by the
        deterministic request-guard path.
        """

        from .ritu_core import (
            get_identity_metadata,
            get_truth_evidence_metadata,
        )

        fields = (
            "id",
            "name",
            "version",
            "category",
            "scope",
            "priority",
            "status",
            "source",
            "canonical_document",
        )

        layers = [
            get_identity_metadata(),
            get_truth_evidence_metadata(),
        ]

        active = [
            layer
            for layer in layers
            if str(layer.get("status") or "").casefold()
            == "active"
        ]

        active.sort(
            key=lambda layer: int(
                layer.get("priority") or 0
            ),
            reverse=True,
        )

        return [
            {
                field: layer.get(field)
                for field in fields
            }
            for layer in active
        ]

    @staticmethod
    def _append_response(
        response: str,
        addition: str,
    ) -> str:
        response = str(response or "").strip()
        addition = str(addition or "").strip()

        if not response:
            return addition

        if not addition:
            return response

        return response + "\n\n" + addition

    @staticmethod
    def _detected_response_key(
        plan: dict[str, Any] | None,
    ) -> str | None:
        if not isinstance(plan, dict):
            return None

        for key in (
            "response",
            "reply",
            "message",
            "answer",
            "text",
        ):
            value = plan.get(key)

            if isinstance(value, str) and value.strip():
                return key

        return None