# Feedback Stage

Before persisting feedback:
1) Detect email identifiers.
2) Request role mapping.
3) Replace identifiers with role tokens.
4) Redact remaining emails.

Output structured fields:
- facts_learned
- decisions_made
- open_questions
- commitments
- blockers
- sentiment (supportive/resistant/confused/neutral)

Persist only sanitized output and role-level memory notes.
