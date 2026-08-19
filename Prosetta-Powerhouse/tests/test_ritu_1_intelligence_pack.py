from __future__ import annotations

from powerhouse.prompt_builder import (
    build_ritu_messages,
)
from powerhouse.response_guard import (
    enforce_truth_contract,
)
from powerhouse.ritu_core import (
    get_agent_orchestration_intelligence,
    get_agent_orchestration_metadata,
    get_approval_governance_intelligence,
    get_approval_governance_metadata,
    get_identity_intelligence,
    get_identity_metadata,
    get_intent_interpretation_intelligence,
    get_intent_interpretation_metadata,
    get_project_formation_intelligence,
    get_project_formation_metadata,
    get_relationship_metadata,
    get_relationship_system_prompt,
    get_security_learning_rca_intelligence,
    get_security_learning_rca_metadata,
    get_spiral_governance_intelligence,
    get_spiral_governance_metadata,
    get_truth_evidence_metadata,
)


EXPECTED_INTELLIGENCE = [
    (
        1000,
        "RITU-CORE-IDENTITY-001",
    ),
    (
        950,
        "RITU-CORE-TRUTH-001",
    ),
    (
        900,
        "RITU-CORE-RELATIONSHIP-001",
    ),
    (
        875,
        "RITU-CORE-INTENT-INTERPRETATION-001",
    ),
    (
        850,
        "RITU-CORE-PROJECT-FORMATION-001",
    ),
    (
        825,
        "RITU-CORE-SPIRAL-GOVERNANCE-001",
    ),
    (
        800,
        "RITU-CORE-AGENT-ORCHESTRATION-001",
    ),
    (
        775,
        "RITU-CORE-APPROVAL-GOVERNANCE-001",
    ),
    (
        750,
        "RITU-CORE-SECURITY-LEARNING-RCA-001",
    ),
]


def _metadata_layers() -> list[dict[str, object]]:
    layers = [
        get_identity_metadata(),
        get_truth_evidence_metadata(),
        get_relationship_metadata(),
        get_intent_interpretation_metadata(),
        get_project_formation_metadata(),
        get_spiral_governance_metadata(),
        get_agent_orchestration_metadata(),
        get_approval_governance_metadata(),
        get_security_learning_rca_metadata(),
    ]

    return sorted(
        layers,
        key=lambda item: int(
            item["priority"]
        ),
        reverse=True,
    )


def _build_test_prompt() -> tuple[
    list[dict[str, str]],
    list[dict[str, object]],
]:
    return build_ritu_messages(
        planner_system=(
            "You are Ritu, Prashant's private personal eCEO "
            "and operating intelligence."
        ),
        room_policy=(
            "Operate truthfully, securely, and within approved limits."
        ),
        company_state={
            "verification": "ritu-1-regression-test",
            "projects": [],
            "agents": [],
        },
        conversation_history=[
            {
                "role": "user",
                "content": "Test project discussion.",
            },
        ],
    )


def test_ritu_1_core_stack_has_nine_active_layers_in_priority_order() -> None:
    layers = _metadata_layers()

    actual = [
        (
            int(layer["priority"]),
            str(layer["id"]),
        )
        for layer in layers
    ]

    assert actual == EXPECTED_INTELLIGENCE

    assert all(
        str(layer["status"]).casefold()
        == "active"
        for layer in layers
    )


def test_identity_and_relationship_use_bounded_authority_versions() -> None:
    identity_metadata = get_identity_metadata()
    relationship_metadata = get_relationship_metadata()

    assert identity_metadata["version"] == "1.1.0"
    assert relationship_metadata["version"] == "1.1.0"

    identity = get_identity_intelligence()
    relationship = get_relationship_system_prompt()

    assert (
        "Prashant retains constitutional"
        in identity
    )
    assert (
        "Ritu has delegated operational authority"
        in identity
    )
    assert (
        "AUTHORITY AND DELEGATION"
        in relationship
    )
    assert (
        "Ritu has delegated operational authority"
        in relationship
    )

    assert (
        "Prashant is the owner and final decision authority"
        not in identity
    )
    assert (
        "Prashant retains final authority over consequential decisions"
        not in relationship
    )


def test_live_prompt_contains_all_ritu_1_layers() -> None:
    messages, active_intelligence = _build_test_prompt()

    actual_ids = [
        str(item["id"])
        for item in active_intelligence
    ]

    expected_ids = [
        intelligence_id
        for _, intelligence_id
        in EXPECTED_INTELLIGENCE
    ]

    assert actual_ids == expected_ids

    system_messages = [
        item
        for item in messages
        if item["role"] == "system"
    ]

    assert len(system_messages) == 12

    combined = "\n\n".join(
        item["content"]
        for item in system_messages
    )

    for intelligence_id in expected_ids:
        assert intelligence_id in combined

    assert (
        "OPERATIONAL ROLE AND ACTION CONTRACT"
        in combined
    )
    assert "CURRENT ROOM POLICY" in combined
    assert (
        "VERIFIED CURRENT POWERHOUSE STATE"
        in combined
    )


def test_intent_interpretation_requires_understanding_before_creation() -> None:
    intelligence = (
        get_intent_interpretation_intelligence()
    )

    required_markers = (
        "what Prashant is trying to achieve",
        "expected user or operating experience",
        "what remains unknown",
        "IMPORTANT QUESTIONS",
        "PROPOSED WAY FORWARD",
        "Ritu must not treat an exploratory discussion as approval",
    )

    for marker in required_markers:
        assert marker in intelligence

    assert (
        "Ritu should not ask Prashant to remember every existing file"
        in intelligence
    )


def test_project_formation_checks_existing_projects_before_creation() -> None:
    intelligence = (
        get_project_formation_intelligence()
    )

    required_markers = (
        "EXISTING PROJECT CHECK",
        "Before proposing a new project",
        "Different wording does not automatically justify a duplicate project",
        "WORKSTREAMS COME BEFORE NEW AGENTS",
        "completion condition",
        "acceptance criteria verified",
    )

    for marker in required_markers:
        assert marker in intelligence


def test_spiral_governance_preserves_context_and_rebriefs_agents() -> None:
    intelligence = (
        get_spiral_governance_intelligence()
    )

    required_markers = (
        "persistent spiral",
        "DISCUSSION CLASSIFICATION",
        "CONTEXT UPDATE",
        "AGENT RE-BRIEFING",
        "Ritu must not silently overwrite",
        "An agent report is not automatically accepted",
        "the next spiral begins",
    )

    for marker in required_markers:
        assert marker in intelligence


def test_agent_orchestration_reuses_existing_agents_before_creation() -> None:
    intelligence = (
        get_agent_orchestration_intelligence()
    )

    required_markers = (
        "inspect existing agents",
        "reuse a suitable agent where possible",
        "create a new agent only when",
        "Ritu must not create ten agents",
        "TASK CONTRACT",
        "Agents report to Ritu",
        "Evidence discipline is a required part of the R&D task",
    )

    for marker in required_markers:
        assert marker in intelligence


def test_approval_governance_classifies_protected_actions() -> None:
    intelligence = (
        get_approval_governance_intelligence()
    )

    required_markers = (
        "AUTONOMOUS",
        "CLARIFICATION REQUIRED",
        "EXPLICIT APPROVAL REQUIRED",
        "PROHIBITED",
        "using a credential or authenticated session",
        "opening or interacting with a logged-in website",
        "installing a package",
        "changing core intelligence",
        "A one-time approval must not silently become",
        "PROHIBITED SELF-APPROVAL",
    )

    for marker in required_markers:
        assert marker in intelligence


def test_security_learning_and_rca_governance_is_complete() -> None:
    intelligence = (
        get_security_learning_rca_intelligence()
    )

    required_markers = (
        "SECURITY BY DESIGN",
        "least privilege",
        "Secrets must not be stored",
        "INFOSEC AND COMPLIANCE RESPONSIBILITY",
        "LEARNING TRACKER",
        "RCA TRIGGERS",
        "RCA TRACKER",
        "corrective action",
        "preventive action",
        "A lesson is not verified merely because it was written down",
    )

    for marker in required_markers:
        assert marker in intelligence


def test_bounded_authority_guard_allows_delegation_and_blocks_self_expansion() -> None:
    safe_response = (
        "Ritu has delegated operational authority within approved limits "
        "to manage projects, agents, tasks, reviews, and routine reversible "
        "operations."
    )

    guarded_safe, safe_violations = enforce_truth_contract(
        response=safe_response,
        user_message=(
            "Explain Ritu's delegated operating authority."
        ),
    )

    assert safe_violations == []
    assert guarded_safe == safe_response

    prohibited_responses = (
        "Ritu has final decision authority over PowerHouse.",
        "Ritu has constitutional authority over PowerHouse.",
        "Ritu holds permission-setting authority over PowerHouse.",
        "Boundary-setting authority remains with Ritu.",
        "Ritu may expand her own authority boundaries.",
    )

    for response in prohibited_responses:
        corrected, violations = enforce_truth_contract(
            response=response,
            user_message=(
                "Explain who controls PowerHouse."
            ),
        )

        assert (
            "authority_hierarchy_violation"
            in violations
        )

        assert (
            "Prashant retains constitutional"
            in corrected
        )

        assert (
            "Ritu has delegated operational authority"
            in corrected
        )


def test_execution_lock_blocks_selected_context_and_no_action_directives():
    from powerhouse.live_orchestrator import (
        action_execution_allowed,
    )

    assert action_execution_allowed(
        "Create a new project.",
        {},
    )

    assert not action_execution_allowed(
        "Create a new project.",
        {
            "execution_allowed": False,
        },
    )

    assert not action_execution_allowed(
        (
            "Explain the authority structure. "
            "Do not create, update, delete, write, install, "
            "train, or change anything. Return no actions."
        ),
        {},
    )


def test_truth_guard_ignores_negated_action_terms():
    from powerhouse.response_guard import (
        enforce_truth_contract,
    )

    response = (
        "Prashant retains constitutional, strategic, "
        "permission-setting, and boundary-setting authority over "
        "PowerHouse. Ritu has delegated operational authority "
        "within approved limits and must escalate actions outside "
        "those limits."
    )

    guarded_response, violations = enforce_truth_contract(
        response=response,
        user_message=(
            "Explain the authority structure. "
            "Do not create, update, delete, write, install, "
            "train, or change anything. Return no actions."
        ),
        successful_outcomes=[],
        file_evidence_available=False,
    )

    assert guarded_response == response
    assert violations == []


def test_current_user_request_is_final_message_with_turn_control():
    from powerhouse.orchestrator import (
        PLANNER_SYSTEM,
    )

    from powerhouse.prompt_builder import (
        build_ritu_messages,
    )

    messages, intelligence = build_ritu_messages(
        planner_system=PLANNER_SYSTEM,
        room_policy="Command room.",
        company_state={
            "tasks": [
                {
                    "title": "Old unrelated OCR task",
                }
            ],
        },
        conversation_history=[
            {
                "role": "user",
                "content": (
                    "Explain the authority structure between "
                    "Prashant, Ritu, and PowerHouse. Return no actions."
                ),
            }
        ],
    )

    assert len(intelligence) == 9
    assert len(messages) == 13

    assert messages[-1]["role"] == "user"
    assert "Explain the authority structure" in messages[-1]["content"]
    assert "## CURRENT TURN CONTROL" in messages[-1]["content"]
    assert "It is the only subject of this turn" in messages[-1]["content"]
    assert "actions must be an empty array" in messages[-1]["content"]

    assert messages[-2]["role"] == "system"
    assert "VERIFIED CURRENT POWERHOUSE STATE" in messages[-2]["content"]

    operational_positions = [
        index
        for index, message in enumerate(messages)
        if (
            message["role"] == "system"
            and "## OPERATIONAL ROLE AND ACTION CONTRACT"
            in message["content"]
        )
    ]

    assert len(operational_positions) == 1
    assert operational_positions[0] < len(messages) - 2


def test_runtime_state_replaces_obsolete_final_authority_phrase():
    from powerhouse.prompt_builder import (
        _format_company_state,
    )

    formatted = _format_company_state(
        {
            "role": (
                "Ritu operates under Prashant's final authority"
            )
        }
    )

    assert "under Prashant's final authority" not in formatted
    assert (
        "within delegated operational authority and approved limits"
        in formatted
    )


def test_model_tier_router_keeps_simple_live_check_fast():
    from powerhouse.live_orchestrator import (
        model_tier_for_request,
    )

    assert (
        model_tier_for_request(
            room="command",
            user_message=(
                "Ritu live check. Say you are available "
                "in one short sentence."
            ),
            selected_context={
                "execution_allowed": False,
            },
        )
        == "fast"
    )


def test_model_tier_router_routes_memory_candidate_to_deep():
    from powerhouse.live_orchestrator import (
        model_tier_for_request,
    )

    assert (
        model_tier_for_request(
            room="command",
            user_message=(
                "Draft a memory candidate for this preference."
            ),
            selected_context={
                "execution_allowed": False,
            },
        )
        == "deep"
    )


def test_model_tier_router_routes_training_and_boardroom_to_deep():
    from powerhouse.live_orchestrator import (
        model_tier_for_request,
    )

    assert (
        model_tier_for_request(
            room="training",
            user_message="Prepare a training brief.",
            selected_context={},
        )
        == "deep"
    )

    assert (
        model_tier_for_request(
            room="boardroom",
            user_message="Review architecture direction.",
            selected_context={},
        )
        == "deep"
    )


def test_model_tier_router_allows_explicit_context_override():
    from powerhouse.live_orchestrator import (
        model_tier_for_request,
    )

    assert (
        model_tier_for_request(
            room="command",
            user_message="Simple note.",
            selected_context={
                "model_tier": "deep",
            },
        )
        == "deep"
    )

    assert (
        model_tier_for_request(
            room="boardroom",
            user_message="Simple note.",
            selected_context={
                "model_tier": "fast",
            },
        )
        == "fast"
    )

