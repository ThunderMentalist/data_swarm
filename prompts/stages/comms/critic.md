# Comms Critic Agent Prompt Spec

## Responsibility
Deterministic critic behavior for the comms stage using typed runtime models.

## Required context
- Stage policy pack (core prompt + cards + trees)
- Stage KB subset
- Upstream stage artifacts relevant to comms
- Run-mode policy switches

## Output contract
Return structured data aligned with stage models/artifacts. Do not auto-apply policy changes.

## Notes
This markdown file is documentation/spec; runtime correctness must not depend on markdown parsing.
