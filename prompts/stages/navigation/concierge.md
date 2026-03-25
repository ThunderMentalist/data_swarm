# Navigation Concierge Agent Prompt Spec

## Responsibility
Deterministic concierge behavior for the navigation stage using typed runtime models.

## Required context
- Stage policy pack (core prompt + cards + trees)
- Stage KB subset
- Upstream stage artifacts relevant to navigation
- Run-mode policy switches

## Output contract
Return structured data aligned with stage models/artifacts. Do not auto-apply policy changes.

## Notes
This markdown file is documentation/spec; runtime correctness must not depend on markdown parsing.
