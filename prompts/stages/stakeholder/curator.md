# Stakeholder Curator Agent Prompt Spec

## Responsibility
Deterministic curator behavior for the stakeholder stage using typed runtime models.

## Required context
- Stage policy pack (core prompt + cards + trees)
- Stage KB subset
- Upstream stage artifacts relevant to stakeholder
- Run-mode policy switches

## Output contract
Return structured data aligned with stage models/artifacts. Do not auto-apply policy changes.

## Notes
This markdown file is documentation/spec; runtime correctness must not depend on markdown parsing.
