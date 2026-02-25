# Definition of Done (DoD) Rubric

A strong DoD makes the task unambiguous, testable, and politically safe.

## DoD checklist
- Outcome is observable and verifiable
- Acceptance criteria are specific (bullets)
- Constraints are explicit (time/data/systems/privacy)
- Approver role(s) are named (role tokens only)
- Non-goals are explicit to prevent scope creep
- Risks/tradeoffs are documented

## Examples
Bad: “Improve the MMM model.”
Better:
- DoD: “Deliver a validated model spec + results summary with channels’ contribution ranges.”
- Acceptance criteria:
  - “Passes QA checks (no negative baseline, stable coefficients).”
  - “Reviewed by Econometrics Director (role).”
  - “Includes limitations and next steps.”
- Non-goals:
  - “Not building production pipeline in this task.”

## Write acceptance criteria as tests
Use “must” language and include thresholds where possible.
