# data_swarm

`data_swarm` is an agentic Task OS for task-centric execution with explicit HITL checkpoints,
local-only stores, structured state transitions, and plugin-based deliverables.

## Features

- Strict task schema + state machine transitions.
- First-class HITL stages (clarification, comms review, patch approvals).
- Cross-cutting JSONL logging per task.
- Local de-identified memory store (SQLite).
- Meridian_Aux deliverable plugin with indexing, evidence packet creation, and patch/test artifacts.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .[dev]

# Initialize local runtime home
DATA_SWARM_HOME=~/.data_swarm data-swarm init

# Create a task
data-swarm task new --title "Fix Meridian Aux bug" --description "Need robust patch generation" --task-type meridian_aux_codegen

# Run task pipeline (interactive)
data-swarm task run <task_id>
```

## DATA_SWARM_HOME layout

`DATA_SWARM_HOME` defaults to `~/.data_swarm` and is the only mutable runtime location:

- `~/.data_swarm/config.yaml`
- `~/.data_swarm/.env` (optional local env file)
- `~/.data_swarm/tasks/...`
- `~/.data_swarm/logs/...`
- `~/.data_swarm/memory/...`
- `~/.data_swarm/indexes/...`

## Meridian path configuration

If omitted, paths are auto-detected as sibling repos:

- `/home/ec2-user/SageMaker/data_swarm`
- `/home/ec2-user/SageMaker/meridian`
- `/home/ec2-user/SageMaker/meridian_aux`

Override in `~/.data_swarm/config.yaml` under `paths.meridian_repo` and `paths.meridian_aux_repo`.

## Example Meridian_Aux workflow

1. Build index: `data-swarm index build`
2. Run task with `task_type=meridian_aux_codegen`
3. Review generated artifacts in:
   - `07_deliverable/evidence/`
   - `07_deliverable/patch.diff`
   - `07_deliverable/test_run.json`

If `OPENAI_API_KEY` is not set, codegen fails gracefully and writes guidance in `07_deliverable/notes.md`.

## Safety notes

- Never commit secrets; API keys are environment-only.
- Memory persistence stores role-level de-identified info only.
- Patch application refuses writes outside configured target repo.
