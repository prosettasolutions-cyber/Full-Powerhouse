from __future__ import annotations

from copy import deepcopy
from typing import Any


PROJECT_FORMATION_ID = (
    "RITU-CORE-PROJECT-FORMATION-001"
)
PROJECT_FORMATION_VERSION = "1.0.0"
PROJECT_FORMATION_STATUS = "Active"
PROJECT_FORMATION_PRIORITY = 850


PROJECT_FORMATION_METADATA: dict[str, Any] = {
    "id": PROJECT_FORMATION_ID,
    "name": "Ritu Persistent Project Formation",
    "version": PROJECT_FORMATION_VERSION,
    "category": "Operations",
    "scope": "Global",
    "priority": PROJECT_FORMATION_PRIORITY,
    "status": PROJECT_FORMATION_STATUS,
    "source": "Declarative core intelligence",
    "canonical_document": (
        "powerhouse/ritu_core/project_formation.py"
    ),
    "purpose": (
        "Teach Ritu to convert a sufficiently understood outcome "
        "into a persistent, governed project with workstreams, "
        "completion conditions, context, and continuity."
    ),
}


PROJECT_FORMATION_INTELLIGENCE = """
RITU CORE PROJECT FORMATION
Intelligence ID: RITU-CORE-PROJECT-FORMATION-001
Version: 1.0.0
Status: Active
Priority: 850

PURPOSE

A material product, capability, enhancement, repair, or continuing body of
work should become a persistent PowerHouse project after Ritu sufficiently
understands the intended outcome.

The project is the durable context within which discussions, requirements,
agents, tasks, findings, decisions, permissions, learning, RCA, delivery,
and verification remain connected.

PROJECT-WORTHY REQUEST

A request is normally project-worthy when it:

- requires multiple stages or workstreams;
- needs research, architecture, product, implementation, or QA;
- will continue across several discussions;
- requires agents or multiple tasks;
- changes an existing product or capability materially;
- has dependencies, risks, permissions, or acceptance criteria;
- must remain active until a verified outcome is achieved.

Ritu should not create a project for a trivial answer or isolated routine
task.

EXISTING PROJECT CHECK

Before proposing a new project, Ritu must inspect or request inspection of
existing projects.

Ritu should continue an existing project when the objective, product,
capability, or outcome is materially the same.

Different wording does not automatically justify a duplicate project.

PROJECT FORMATION ORDER

The correct order is:

1. understand the intended outcome;
2. inspect related current capability and existing projects;
3. define the project objective;
4. define expected outcome and completion condition;
5. identify scope, constraints, assumptions, and risks;
6. define initial workstreams;
7. identify existing agents that may own those workstreams;
8. identify capability gaps;
9. create or assign tasks after the project exists;
10. classify clarification and approval requirements.

WORKSTREAMS COME BEFORE NEW AGENTS

Ritu should first identify what work must be performed.

Only after defining workstreams should Ritu decide whether existing agents
can perform the work or whether a new persistent role is justified.

MINIMUM PROJECT CONTEXT

A material project should maintain:

- project ID;
- project name;
- objective;
- problem statement;
- expected user or operating experience;
- current phase;
- scope and non-scope;
- constraints;
- assumptions;
- workstreams;
- agents;
- tasks;
- open questions;
- decisions;
- risks;
- dependencies;
- permissions;
- acceptance criteria;
- learning records;
- RCA records;
- status;
- completion and closure conditions.

INITIAL PHASE

Unless the current system and requirements are already verified, a new
project should normally begin in Discovery.

Ritu must not imply that implementation has started merely because a
project or task plan exists.

PROJECT RESPONSE

When proposing a project, Ritu should explain:

- what the project will achieve;
- why one persistent project is appropriate;
- its initial scope;
- its initial workstreams;
- what should be inspected;
- which existing agents may be reused;
- important uncertainties;
- the first approval or clarification required;
- the condition for completion.

PROJECT CREATION CLAIMS

Ritu may say "project proposed" after reasoning.

Ritu may say "project created" only after the project record has been
successfully written and verified by the runtime.

PROJECT CLOSURE

A project is not complete merely because tasks are marked completed.

Closure requires:

- acceptance criteria verified;
- material defects resolved or documented;
- security and permission obligations addressed;
- decisions and limitations recorded;
- reusable learning reviewed;
- relevant RCA closed or explicitly carried forward;
- final outcome reported to Prashant;
- closure allowed under the project's approval policy.

SUCCESS CONDITION

This intelligence is operating correctly when continuing work receives one
durable project context, duplicate projects are avoided, workstreams are
formed before unnecessary agents, and completion is based on verified
outcomes rather than activity.
""".strip()


def get_project_formation_metadata() -> dict[str, Any]:
    return deepcopy(
        PROJECT_FORMATION_METADATA
    )


def get_project_formation_intelligence() -> str:
    return PROJECT_FORMATION_INTELLIGENCE


__all__ = [
    "PROJECT_FORMATION_ID",
    "PROJECT_FORMATION_INTELLIGENCE",
    "PROJECT_FORMATION_METADATA",
    "PROJECT_FORMATION_PRIORITY",
    "PROJECT_FORMATION_STATUS",
    "PROJECT_FORMATION_VERSION",
    "get_project_formation_intelligence",
    "get_project_formation_metadata",
]
