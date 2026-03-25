# Planner Stage Spec

## Purpose
Produce a structured execution plan grounded in triage outputs.

## Inputs
- `01_triage/final_brief.json`
- planner policy + KB subset

## Outputs
- `02_plan/02_plan.json`
- critic / curator / change artifacts

## Approval semantics
- Operator approval required.
- Approved planner owns transition to `PLANNED`.

## Sub-agents
Concierge, Critic, Curator, Change as defined in `prompts/stages/planner/*.md`.
