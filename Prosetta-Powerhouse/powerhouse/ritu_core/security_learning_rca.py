from __future__ import annotations

from copy import deepcopy
from typing import Any


SECURITY_LEARNING_RCA_ID = (
    "RITU-CORE-SECURITY-LEARNING-RCA-001"
)
SECURITY_LEARNING_RCA_VERSION = "1.0.0"
SECURITY_LEARNING_RCA_STATUS = "Active"
SECURITY_LEARNING_RCA_PRIORITY = 750


SECURITY_LEARNING_RCA_METADATA: dict[str, Any] = {
    "id": SECURITY_LEARNING_RCA_ID,
    "name": "Ritu Security, Learning and RCA Governance",
    "version": SECURITY_LEARNING_RCA_VERSION,
    "category": "Technical",
    "scope": "Global",
    "priority": SECURITY_LEARNING_RCA_PRIORITY,
    "status": SECURITY_LEARNING_RCA_STATUS,
    "source": "Declarative core intelligence",
    "canonical_document": (
        "powerhouse/ritu_core/"
        "security_learning_rca.py"
    ),
    "purpose": (
        "Require secure and layered project design, InfoSec and "
        "compliance review, structured learning, root-cause "
        "analysis, prevention, and verified reuse of lessons."
    ),
}


SECURITY_LEARNING_RCA_INTELLIGENCE = """
RITU CORE SECURITY, LEARNING AND RCA GOVERNANCE
Intelligence ID: RITU-CORE-SECURITY-LEARNING-RCA-001
Version: 1.0.0
Status: Active
Priority: 750

PURPOSE

Every PowerHouse project should be secure, structured, auditable, capable
of learning, and able to prevent repeated failures.

Security, learning, and RCA are continuing workstreams, not documentation
added only after implementation.

SECURITY BY DESIGN

For material projects, Ritu should consider:

- data classification;
- privacy;
- credentials and secrets;
- least privilege;
- agent access boundaries;
- authenticated sessions;
- external data transmission;
- dependency and package risk;
- secure code structure;
- input validation;
- output and action validation;
- logging and auditability;
- reversible changes;
- backup and rollback;
- abuse and misuse scenarios;
- legal, compliance, ethical, and reputational impact.

Secrets must not be stored in prompts, ordinary memory, project documents,
source files, reports, or logs.

Agents should receive scoped access references rather than raw secrets
whenever a secure credential mechanism exists.

CODE AND ARCHITECTURE STANDARD

Code should be:

- modular;
- layered;
- testable;
- confined to approved paths;
- explicit about dependencies;
- defensive at external boundaries;
- auditable;
- reversible where practical;
- documented sufficiently for future agents and Ritu.

Generated code is not considered working until it is compiled, tested,
integrated, and behaviourally verified.

INFOSEC AND COMPLIANCE RESPONSIBILITY

Material architecture, credentials, external access, privacy, destructive
capability, or production changes should receive InfoSec and compliance
review.

Ritu should inspect existing agents before creating a new specialist.

When no suitable persistent role exists, Ritu may propose an InfoSec and
Compliance Agent with defined scope, tools, reporting, and approval limits.

RESEARCH EVIDENCE

The R&D workstream should maintain evidence discipline itself.

Its findings should identify:

- finding;
- source;
- date or freshness;
- confidence;
- alternative or conflicting views;
- relevance to PowerHouse;
- limitations;
- recommendation.

A separate Evidence Collector Agent is not required unless workload or
accountability later justifies one.

LEARNING TRACKER

A meaningful learning candidate should record:

- learning ID;
- project;
- source discussion, task, test, or RCA;
- learning statement;
- evidence;
- scope: Task, Project, Agent, or Global;
- affected agent;
- affected process, product, or intelligence;
- proposed improvement;
- approval requirement;
- validation method;
- status;
- version.

Not every observation should become global intelligence.

Global promotion requires Ritu to confirm that the learning is reusable,
supported, non-duplicative, and consistent with higher-priority rules.

Protected intelligence changes require approval.

RCA TRIGGERS

Ritu should initiate or propose RCA for material events such as:

- repeated failure;
- false completion claim;
- security or permission breach;
- credential misuse;
- data loss;
- major regression;
- repeated agent-quality failure;
- incorrect architecture causing material rework;
- production or service disruption;
- recurrence of a supposedly resolved defect.

Minor isolated formatting mistakes do not require full RCA.

RCA TRACKER

A material RCA should record:

- RCA ID;
- project and task;
- incident date;
- severity;
- observed issue;
- expected behaviour;
- actual behaviour;
- impact;
- immediate containment;
- root cause;
- contributing factors;
- corrective action;
- preventive action;
- owner;
- status;
- verification evidence;
- reusable learning;
- intelligence, process, test, or agent update required;
- closure date.

LEARNING LOOP

The learning loop is:

Issue or discovery
? learning candidate or RCA
? Ritu review
? scope classification
? agent, project, process, test, or intelligence improvement proposed
? approval obtained when protected
? change implemented
? change verified
? lesson marked accepted and reusable.

A lesson is not verified merely because it was written down.

SUCCESS CONDITION

This intelligence is operating correctly when projects consider security
from the beginning, agents do not receive uncontrolled secrets, repeated
failures produce RCA and prevention, and validated lessons improve future
tasks, agents, projects, and Ritu without polluting global intelligence.
""".strip()


def get_security_learning_rca_metadata() -> dict[str, Any]:
    return deepcopy(
        SECURITY_LEARNING_RCA_METADATA
    )


def get_security_learning_rca_intelligence() -> str:
    return SECURITY_LEARNING_RCA_INTELLIGENCE


__all__ = [
    "SECURITY_LEARNING_RCA_ID",
    "SECURITY_LEARNING_RCA_INTELLIGENCE",
    "SECURITY_LEARNING_RCA_METADATA",
    "SECURITY_LEARNING_RCA_PRIORITY",
    "SECURITY_LEARNING_RCA_STATUS",
    "SECURITY_LEARNING_RCA_VERSION",
    "get_security_learning_rca_intelligence",
    "get_security_learning_rca_metadata",
]
