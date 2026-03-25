# Triage Stage Spec

## Purpose
Turn intake into a complete, policy-compliant task brief and identify requested attachment extraction.

## Inputs
- `00_intake/refined_task.md`
- attachment inventory
- triage policy pack
- triage KB subset
- optional memory preferences

## Outputs
- `01_triage/final_brief.json`
- `01_triage/requested_attachment_extraction.json`
- critic / curator / change artifacts

## Approval semantics
- Operator approval required to finalize and transition to `TRIAGED`.

## Sub-agents
- Concierge: build/update `TaskBrief`.
- Critic: score completeness + policy compliance.
- Curator: create durable candidates/delta summary.
- Change: write proposal/history artifacts only (no auto policy apply).
