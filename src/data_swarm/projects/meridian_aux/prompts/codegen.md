# Meridian_Aux Codegen Prompt

Return YAML/JSON with keys:
- patch: unified diff targeting meridian_aux repo only
- tests_added: list of tests added/updated
- snippet: runnable python snippet
- notes: concise rationale

Constraints:
- Touch meridian_aux files only.
- Follow existing patterns, use type hints/docstrings for public functions.
- Add/adjust tests and __init__.py exports when needed.
- Minimize dependencies.
