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

Stages: intake → triage → planner → stakeholder → navigation → comms → feedback → deliverable.

State machine: `NEW -> NEEDS_CLARIFICATION -> PLANNED -> OUTREACH_PENDING_REVIEW -> AWAITING_REPLIES -> READY_TO_DELIVER -> DELIVERED` (plus `REPLANNING/BLOCKED/CLOSED` branches).
All state changes are validated and persisted with `state_transition` JSONL events.

## HITL modes

1. **Clarification loop:** triage questions, then explicit approval to proceed.
2. **Comms review:** drafts are generated per channel and both draft + approved copies are stored.
3. **Code/bug approvals:** patch approval before apply, and additional approval after test failures before debug iteration.

## Privacy model

- Identifiers may be seen during active session.
- Feedback persistence is sanitized after role mapping.
- Memory store receives role-level notes only (no names/emails).
- Mapping tables are not persisted; only sanitized output is stored.

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

This creates config defaults, richer tone profile template, and `.env` placeholder.

`data-swarm init` also seeds `~/.data_swarm/kb/` with local-only YAML templates:

- `org_units.yaml`
- `role_registry.yaml`
- `stakeholder_profiles.yaml`
- `politics_map.yaml`
- `comms_patterns.yaml`

The KB is role-token-only (no names/emails) and is the single local place to edit
stakeholder, navigation, and comms context. Prompts assume this KB exists, but they
still operate if files are missing/sparse.

## SageMaker sibling repo layout

Default auto-detection expects sibling repositories:

- `/home/ec2-user/SageMaker/data_swarm`
- `/home/ec2-user/SageMaker/meridian`
- `/home/ec2-user/SageMaker/meridian_aux`

Override paths in `~/.data_swarm/config.yaml` under `paths`.

## Meridian_Aux plugin flow

1. Build index over **both** `meridian` and `meridian_aux`.
2. Navigator selects entrypoints.
3. Dependency closure follows import edges (bounded by `max_files` and `max_chars`).
4. Evidence packet writes snippets, import edges, and `evidence/context.md` summary.
5. Codegen proposes patch/snippet/tests; patch summary shown before approval.
6. Snippet + pytest run.
7. On failure, traceback artifacts are stored and bounded debug loop runs (default 3 iterations) with approval before each iteration and debug patch apply.
8. Final summary written to `07_deliverable/summary.md`.
