from __future__ import annotations

import re
from typing import Any


_RESPONSE_KEYS = (
    "response",
    "reply",
    "message",
    "answer",
    "text",
)


_STRUCTURED_RESPONSE_KEYS = (
    "role",
    "final_decision_authority",
    "recommendation",
    "reason",
    "rationale",
    "summary",
    "status",
    "decision",
    "result",
    "explanation",
)


_STRUCTURED_RESPONSE_LABELS = {
    "role": "Role",
    "final_decision_authority": "Final decision authority",
    "recommendation": "Recommendation",
    "reason": "Reason",
    "rationale": "Rationale",
    "summary": "Summary",
    "status": "Status",
    "decision": "Decision",
    "result": "Result",
    "explanation": "Explanation",
}


_ACTION_VERBS = (
    "update",
    "create",
    "delete",
    "remove",
    "move",
    "rename",
    "write",
    "save",
    "install",
    "execute",
    "send",
    "upload",
    "download",
    "log in",
    "navigate",
    "modify",
    "patch",
    "change",
)


_ACTION_FORMS = {
    "update": ("update", "updated", "updating"),
    "create": ("create", "created", "creating"),
    "delete": ("delete", "deleted", "deleting"),
    "remove": ("remove", "removed", "removing"),
    "move": ("move", "moved", "moving"),
    "rename": ("rename", "renamed", "renaming"),
    "write": ("write", "written", "wrote", "writing"),
    "save": ("save", "saved", "saving"),
    "install": ("install", "installed", "installing"),
    "execute": ("execute", "executed", "executing"),
    "send": ("send", "sent", "sending"),
    "upload": ("upload", "uploaded", "uploading"),
    "download": ("download", "downloaded", "downloading"),
    "log in": ("log in", "logged in", "logging in"),
    "navigate": ("navigate", "navigated", "navigating"),
    "modify": ("modify", "modified", "modifying"),
    "patch": ("patch", "patched", "patching"),
    "change": ("change", "changed", "changing"),
}


_INSPECTION_VERBS = (
    "reviewed",
    "read",
    "inspected",
    "analysed",
    "analyzed",
    "examined",
    "checked",
)


_FILE_EXTENSIONS = (
    "py",
    "js",
    "html",
    "css",
    "md",
    "json",
    "txt",
    "yaml",
    "yml",
    "toml",
    "ini",
    "cfg",
    "csv",
    "xlsx",
    "pdf",
)


_FILE_EXTENSION_PATTERN = "|".join(
    re.escape(extension)
    for extension in _FILE_EXTENSIONS
)


_UNVERIFIED_INSPECTION_PATTERNS = (
    rf"\bi\s+(?:have\s+)?(?:successfully\s+)?"
    rf"(?:{'|'.join(_INSPECTION_VERBS)})"
    rf"(?:\s+and\s+(?:{'|'.join(_INSPECTION_VERBS)}))*"
    rf"\s+(?:the\s+)?(?:content\s+of\s+)?"
    rf"[`'\"]?[\w./\\ -]+\."
    rf"(?:{_FILE_EXTENSION_PATTERN})[`'\"]?",

    rf"\bi\s+(?:have\s+)?(?:successfully\s+)?"
    rf"(?:{'|'.join(_INSPECTION_VERBS)})"
    rf"(?:\s+and\s+(?:{'|'.join(_INSPECTION_VERBS)}))*"
    rf"\s+(?:the\s+)?(?:file|code|document|script)\b",

    r"\bthe\s+(?:file|code|document|script)\s+"
    r"(?:appears|looks|seems)\s+to\s+be\b",

    r"\bthe\s+code\s+(?:appears|looks|seems)\s+to\s+be\s+"
    r"(?:correct|correctly\s+formatted|functional|valid|working|"
    r"properly\s+structured)\b",
)


_FALSE_CLAIM_REQUEST_MARKERS = (
    "tell me that you successfully",
    "say that you successfully",
    "claim that you successfully",
    "pretend that you",
    "even though no",
    "without performing",
    "without doing",
    "although no",
)


_NEGATION_MARKERS = (
    "cannot confirm",
    "can't confirm",
    "cannot verify",
    "can't verify",
    "not verified",
    "not completed",
    "was not updated",
    "were not updated",
    "has not been updated",
    "have not been updated",
    "was not created",
    "was not deleted",
    "was not changed",
    "did not update",
    "did not create",
    "did not delete",
    "did not change",
    "no file operation",
    "no actual file operation",
    "no verified action",
    "no verified change",
    "unknown",
    "proposed",
)


_RITU_FINAL_AUTHORITY_PATTERNS = (
    r"\bfinal\s+(?:decision\s+)?authority\s+"
    r"(?:rests|lies|remains)\s+with\s+ritu\b",

    r"\britu\s+(?:has|holds|retains|possesses|is)\s+(?:the\s+)?"
    r"final\s+(?:decision\s+)?authority\b",

    r"\bfinal_decision_authority\s*[:=]\s*[`'\"]?ritu\b",

    r"\bfinal\s+decision\s+authority\s*:\s*ritu\b",

    r"\b(?:constitutional|strategic|permission-setting|"
    r"boundary-setting)\s+authority\s+"
    r"(?:rests|lies|remains)\s+with\s+ritu\b",

    r"\britu\s+(?:has|holds|retains|possesses|is)\s+(?:the\s+)?"
    r"(?:constitutional|strategic|permission-setting|"
    r"boundary-setting)\s+authority\b",

    r"\bconstitutional_authority\s*[:=]\s*[`'\"]?ritu\b",

    r"\bpermission_setting_authority\s*[:=]\s*[`'\"]?ritu\b",

    r"\bboundary_setting_authority\s*[:=]\s*[`'\"]?ritu\b",

    r"\britu\s+(?:may|can|will)\s+"
    r"(?:set|change|expand|approve)\s+(?:her|its)\s+own\s+"
    r"(?:authority|permission|operating)\s+"
    r"(?:limits|boundaries)\b",
)


def normalize_model_plan(
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Convert model output into Ritu's canonical response contract.

    Normalization order:

    1. Use an approved direct response key.
    2. Otherwise compose a response from a restricted set of semantic fields.
    3. Never turn action metadata, booleans, IDs, nested objects, or arbitrary
       internal JSON into a user-facing answer.

    Normalization does not establish truth. The resulting response must still
    pass enforce_truth_contract().
    """

    source = plan if isinstance(plan, dict) else {}

    response = ""

    for key in _RESPONSE_KEYS:
        value = source.get(key)

        if isinstance(value, str) and value.strip():
            response = value.strip()
            break

    if not response:
        response = _structured_response_fallback(
            source
        )

    actions = source.get("actions")

    if not isinstance(actions, list):
        actions = []

    normalized = {
        "response": response,
        "needs_input": bool(
            source.get("needs_input")
        ),
        "actions": actions,
    }

    for key, value in source.items():
        if key not in normalized:
            normalized[key] = value

    return normalized


def enforce_truth_contract(
    *,
    response: str,
    user_message: str,
    successful_outcomes: list[dict[str, Any]] | None = None,
    file_evidence_available: bool = False,
) -> tuple[str, list[str]]:
    """
    Enforce deterministic truth, authority, evidence, and action alignment.

    The guard distinguishes between:

    - inspecting a file;
    - proposing a change;
    - performing a verified change;
    - advising Prashant;
    - claiming final, constitutional, strategic, permission-setting, or boundary-setting authority.

    File-read evidence never proves that a file-write action occurred.
    Ritu never becomes the constitutional, strategic, permission-setting, or boundary-setting authority.
    """

    successful = successful_outcomes or []
    text = str(response or "").strip()
    request = str(user_message or "").strip()

    violations: list[str] = []

    if not text:
        return (
            "UNKNOWN: The model did not return a usable response. "
            "No action or completion has been verified.",
            ["missing_response"],
        )

    if _matches_any(
        text,
        _RITU_FINAL_AUTHORITY_PATTERNS,
    ):
        violations.append(
            "authority_hierarchy_violation"
        )

    requested_actions = _detect_requested_actions(
        request
    )

    verified_action_types = _successful_action_types(
        successful
    )

    if (
        _is_false_completion_request(request)
        and not successful
    ):
        violations.append(
            "requested_false_completion_claim"
        )

    for requested_action in requested_actions:
        if _action_is_verified(
            requested_action,
            verified_action_types,
        ):
            continue

        if not _response_explicitly_denies_action(
            text,
            requested_action,
        ):
            violations.append(
                f"unverified_requested_action:{requested_action}"
            )

    if (
        not file_evidence_available
        and _matches_any(
            text,
            _UNVERIFIED_INSPECTION_PATTERNS,
        )
    ):
        violations.append(
            "unsupported_file_inspection_claim"
        )

    violations = list(
        dict.fromkeys(violations)
    )

    if (
        "authority_hierarchy_violation"
        in violations
    ):
        return (
            _authority_correction(),
            violations,
        )

    if violations:
        return (
            _truthful_rejection(
                user_message=request,
                requested_actions=requested_actions,
                violations=violations,
                file_evidence_available=file_evidence_available,
            ),
            violations,
        )

    return text, []


def has_file_evidence(
    company_state: dict[str, Any] | None,
) -> bool:
    """
    Return True only when runtime state contains actual file-read evidence.

    File-read evidence supports inspection claims only. It does not prove that
    any file update, creation, deletion, or other write action occurred.
    """

    if not isinstance(company_state, dict):
        return False

    evidence_fields = (
        "project_workspace",
        "portal_source",
        "file_content",
        "verified_file",
        "artifact",
    )

    return any(
        bool(company_state.get(field))
        for field in evidence_fields
    )


def guard_user_request(
    user_message: str,
) -> tuple[bool, str, list[str]]:
    """
    Block requests that explicitly ask Ritu to make a false completion claim.
    """

    message = str(
        user_message or ""
    ).strip()

    lowered = message.casefold()

    false_claim_markers = (
        "tell me that you successfully",
        "say that you successfully",
        "claim that you successfully",
        "pretend that you successfully",
        "confirm that you successfully",
        "even though no file operation",
        "even though no action",
        "although no file operation",
        "without performing the action",
        "without performing any action",
        "without actually doing it",
    )

    requested_actions = _detect_requested_actions(
        message
    )

    explicitly_requests_false_claim = any(
        marker in lowered
        for marker in false_claim_markers
    )

    if not explicitly_requests_false_claim:
        return True, "", []

    action_text = (
        ", ".join(requested_actions)
        if requested_actions
        else "requested action"
    )

    response = (
        "NOT COMPLETED: I will not make a false completion claim. "
        f"The {action_text} was not performed and no matching successful "
        "runtime action was verified."
    )

    return (
        False,
        response,
        ["explicit_false_completion_request"],
    )


def _structured_response_fallback(
    source: dict[str, Any],
) -> str:
    """
    Compose a readable response from approved semantic string fields.

    Only explicitly approved keys are accepted. Values must be short, scalar
    strings. Nested structures, lists, booleans, numeric values, action data,
    internal identifiers, and arbitrary keys are excluded.
    """

    parts: list[str] = []

    for key in _STRUCTURED_RESPONSE_KEYS:
        value = source.get(key)

        if not isinstance(value, str):
            continue

        cleaned = " ".join(
            value.split()
        ).strip()

        if not cleaned:
            continue

        if len(cleaned) > 1500:
            continue

        label = _STRUCTURED_RESPONSE_LABELS[
            key
        ]

        parts.append(
            f"{label}: {cleaned}"
        )

    return "\n".join(parts)


def _detect_requested_actions(
    user_message: str,
) -> list[str]:
    lowered = str(
        user_message or ""
    ).casefold()

    detected: list[str] = []

    for action, forms in _ACTION_FORMS.items():
        action_detected = False

        for form in forms:
            for match in re.finditer(
                rf"\b{re.escape(form)}\b",
                lowered,
            ):
                if _action_mention_is_negated(
                    lowered,
                    match.start(),
                ):
                    continue

                action_detected = True
                break

            if action_detected:
                break

        if action_detected:
            detected.append(action)

    return detected


def _action_mention_is_negated(
    lowered_message: str,
    action_start: int,
) -> bool:
    """
    Return True when an action term belongs to a negative instruction.

    Example:
    Do not create, update, delete, write, install, or change anything.
    """

    sentence_boundaries = (
        lowered_message.rfind(
            ".",
            0,
            action_start,
        ),
        lowered_message.rfind(
            "!",
            0,
            action_start,
        ),
        lowered_message.rfind(
            "?",
            0,
            action_start,
        ),
        lowered_message.rfind(
            "\n",
            0,
            action_start,
        ),
    )

    segment_start = max(
        sentence_boundaries
    ) + 1

    prefix = lowered_message[
        segment_start:action_start
    ]

    negation_matches = list(
        re.finditer(
            (
                r"\b(?:"
                r"do\s+not|"
                r"don't|"
                r"must\s+not|"
                r"should\s+not|"
                r"cannot|"
                r"can't|"
                r"never|"
                r"without"
                r")\b"
            ),
            prefix,
        )
    )

    if not negation_matches:
        return False

    latest_negation = negation_matches[-1].start()

    contrast_matches = list(
        re.finditer(
            r"\b(?:but|however|instead|except)\b",
            prefix,
        )
    )

    if (
        contrast_matches
        and contrast_matches[-1].start()
        > latest_negation
    ):
        return False

    return True


def _successful_action_types(
    outcomes: list[dict[str, Any]],
) -> set[str]:
    action_types: set[str] = set()

    for outcome in outcomes:
        if not isinstance(outcome, dict):
            continue

        if outcome.get("ok") is not True:
            continue

        if outcome.get("verified", True) is not True:
            continue

        raw_type = str(
            outcome.get("type") or ""
        ).casefold()

        summary = str(
            outcome.get("summary") or ""
        ).casefold()

        combined = f"{raw_type} {summary}"

        for action, forms in _ACTION_FORMS.items():
            if any(
                form in combined
                for form in forms
            ):
                action_types.add(action)

    return action_types


def _action_is_verified(
    requested_action: str,
    verified_action_types: set[str],
) -> bool:
    equivalent_actions = {
        "update": {
            "update",
            "modify",
            "patch",
            "change",
            "write",
            "save",
        },
        "modify": {
            "modify",
            "update",
            "patch",
            "change",
            "write",
            "save",
        },
        "patch": {
            "patch",
            "modify",
            "update",
            "change",
            "write",
            "save",
        },
        "change": {
            "change",
            "modify",
            "update",
            "patch",
            "write",
            "save",
        },
        "write": {
            "write",
            "save",
            "create",
            "update",
            "modify",
            "patch",
        },
        "save": {
            "save",
            "write",
            "create",
            "update",
            "modify",
            "patch",
        },
        "create": {
            "create",
            "write",
            "save",
        },
        "delete": {
            "delete",
            "remove",
        },
        "remove": {
            "remove",
            "delete",
        },
    }

    acceptable = equivalent_actions.get(
        requested_action,
        {requested_action},
    )

    return bool(
        acceptable
        & verified_action_types
    )


def _response_explicitly_denies_action(
    response: str,
    requested_action: str,
) -> bool:
    lowered = response.casefold()

    if any(
        marker in lowered
        for marker in _NEGATION_MARKERS
    ):
        return True

    forms = _ACTION_FORMS.get(
        requested_action,
        (requested_action,),
    )

    escaped_forms = "|".join(
        re.escape(form)
        for form in forms
    )

    denial_patterns = (
        rf"\bdid\s+not\s+(?:{escaped_forms})\b",
        rf"\bnot\s+(?:{escaped_forms})\b",
        rf"\bno\s+verified\s+(?:{escaped_forms})\b",
    )

    return _matches_any(
        response,
        denial_patterns,
    )


def _is_false_completion_request(
    user_message: str,
) -> bool:
    lowered = user_message.casefold()

    return any(
        marker in lowered
        for marker in _FALSE_CLAIM_REQUEST_MARKERS
    )


def _matches_any(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _authority_correction() -> str:
    return (
        "CORRECTION: Prashant retains constitutional, strategic, "
        "permission-setting, and boundary-setting authority over "
        "PowerHouse. Ritu has delegated operational authority within "
        "approved limits. Within those limits, Ritu may manage projects, "
        "agents, tasks, research, reviews, documentation, learning, RCA, "
        "and routine reversible operations. Ritu must escalate credentials, "
        "authenticated-site access, new applications or dependencies, "
        "protected core changes, destructive or irreversible actions, "
        "external commitments, material security or compliance risk, "
        "and any expansion of authority boundaries."
    )


def _truthful_rejection(
    *,
    user_message: str,
    requested_actions: list[str],
    violations: list[str],
    file_evidence_available: bool,
) -> str:
    action_text = (
        ", ".join(requested_actions)
        if requested_actions
        else "requested action"
    )

    inspection_note = ""

    if file_evidence_available:
        inspection_note = (
            " Verified file content may have been available for inspection, "
            "but inspecting a file does not constitute modifying it."
        )

    return (
        f"NOT COMPLETED: I cannot truthfully claim that the {action_text} "
        "was performed because no matching successful runtime action was "
        "verified."
        f"{inspection_note} "
        "No verified file change has occurred."
    )