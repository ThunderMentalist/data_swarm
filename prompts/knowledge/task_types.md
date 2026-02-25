# Task Types and Routing Guide

This page standardizes task classification and which pipeline actions to emphasize.

## Core taxonomy
- meridian_aux_codegen:
  - Goal: propose and apply code changes in meridian_aux using evidence packets + HITL patch approvals.
  - Typical artifacts: evidence packet, patch.diff, tests, snippet, test outputs.
- analysis_request:
  - Goal: analysis/modelling/synthesis. Emphasize DoD, data access, validation.
  - Typical artifacts: analysis plan, assumptions/unknowns, results summary.
- data_request:
  - Goal: obtain data access/extract. Emphasize permissions, governance, timelines.
- stakeholder_outreach:
  - Goal: alignment and buy-in. Emphasize stakeholder map, navigation, comms.
- incident_debug:
  - Goal: urgent restore service. Emphasize timebox, escalation, rollback plan.
- planning_only:
  - Goal: plan/brief only. No execution without explicit follow-up task.
- other:
  - Must define routing explicitly and why it doesn’t fit.

## Routing heuristics
- If code change needed → meridian_aux_codegen (or future plugin)
- If unclear success criteria → triage clarification until DoD is explicit
- If multiple teams involved → stakeholder + navigation emphasized
- If approvals needed → identify decision rights early (triage + planner)

## Common anti-patterns to avoid
- Vague outcomes (“make it better”)
- No approver role identified
- No data provenance / access plan
- Assuming silent stakeholders are aligned
