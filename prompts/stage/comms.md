# Comms Stage Spec

## Purpose
Produce channel-level approved communications aligned to navigation and stakeholder plans.

## Inputs
- navigation, stakeholder, planner, triage artifacts
- comms KB subset + policy
- memory preferences where available

## Outputs
- `05_comms/final_comms.json`
- critic / curator / change artifacts

## Approval semantics
- Channel-by-channel operator review required.
- Approved stage transitions toward outreach/replies (`OUTREACH_PENDING_REVIEW` then `AWAITING_REPLIES`).

## Sub-agents
Concierge, Critic, Curator, Change.
