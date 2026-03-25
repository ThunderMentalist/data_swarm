# data_swarm

`data_swarm` is an agentic Task OS for task-centric execution with explicit HITL checkpoints,
validated state transitions, local JSONL logs, and plugin-based deliverables.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .[dev]
# Optional LLM integration
python -m pip install -e .[openai]
# or both
python -m pip install -e .[dev,openai]
```

## Pipeline stages and states

Main pipeline: `intake -> triage -> planner -> stakeholder -> navigation -> comms`.

Reply handling stage: `reaction` (single reply-ingestion path; legacy `feedback` is removed).

Readiness + deliverable flow:
- `AWAITING_REPLIES` runs `reaction`, then readiness evaluation.
- readiness recommendation can be `AWAITING_REPLIES`, `REPLANNING`, or `READY_TO_DELIVER`.
- `READY_TO_DELIVER` is required before deliverable execution.
- deliverable completion transitions to `DELIVERED`.

State machine backbone:
`NEW -> TRIAGED -> PLANNED -> OUTREACH_PENDING_REVIEW -> AWAITING_REPLIES -> READY_TO_DELIVER -> DELIVERED`
with `NEEDS_CLARIFICATION`, `REPLANNING`, `BLOCKED`, and `CLOSED` branches.

## HITL modes

1. **Triage stage approval gate:** triage questions run until explicit approval to proceed.
2. **Comms review:** drafts are generated per channel and both draft + approved copies are stored.
3. **Readiness approval:** readiness recommendations are shown and require operator approval by default.
4. **Code/bug approvals:** patch approval before apply, and approval before each debug iteration.

## DATA_SWARM_HOME and local config

`DATA_SWARM_HOME` defaults to `~/.data_swarm` and is the single editable location:

- `~/.data_swarm/config.yaml`
- `~/.data_swarm/tone_profile.md`
- `~/.data_swarm/.env` (commented placeholders only)
- `~/.data_swarm/tasks/`, `logs/`, `memory/`, `indexes/`

Run:

```bash
data-swarm init
```

This creates config defaults, tone profile template, and `.env` placeholder.

`data-swarm init` also seeds `~/.data_swarm/kb/` with local-only YAML templates:

- `org_units.yaml`
- `role_registry.yaml`
- `stakeholder_profiles.yaml`
- `politics_map.yaml`
- `comms_patterns.yaml`
- `personas.yaml`

KB and stage policy packs are consumed by runtime logic (not just logging) to shape
stage outputs, compliance scoring, and deterministic constraints.
