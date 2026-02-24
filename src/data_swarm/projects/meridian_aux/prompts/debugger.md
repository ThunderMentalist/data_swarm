# Meridian_Aux Debugger Prompt

Return YAML/JSON object with keys:
- patch: unified diff (meridian_aux only)
- probe_snippet: optional snippet for focused repro
- notes: debugging rationale and stop conditions

Constraints:
- Keep patch scoped to meridian_aux only.
- Prefer small deterministic fixes.
