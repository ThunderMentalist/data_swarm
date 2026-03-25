# Reaction Stage Spec

## Purpose
Ingest external replies, update triage patch artifacts, and provide readiness recommendation.

## Inputs
- external reply summary (operator supplied)
- upstream artifacts for impact/readiness context
- reaction KB subset + policy

## Outputs
- `06_reaction/final_reaction.json`
- `06_reaction/triage_update_patch.json`
- `06_reaction/readiness_recommendation.json`

## Approval semantics
- Manual approval required for stage completion.
- Readiness recommendation requires operator approval by default.

## Sub-agents
Concierge, Critic, Curator, Change semantics are documented for reaction under `prompts/stages/reaction/*`.
