# AGENTS.md

## Repository expectations
- Keep changes small and readable: prefer small modules and clear naming.
- Use type hints where practical and write docstrings for public functions.
- Do not introduce large new dependencies without explicitly stating why.

## Setup and run
- If `pyproject.toml` exists, follow its documented workflow (e.g., poetry/uv).
- If `requirements.txt` exists, use:
  - `python -m venv .venv`
  - `python -m pip install -r requirements.txt`
- If neither exists, avoid guessing tooling; ask or keep changes self-contained.

## Quality gates (only run what exists)
- If a test runner is present, run the project’s tests before opening a PR.
- If lint/format tools exist in the repo, run them before opening a PR.
- If no tooling exists yet, keep the change minimal and explain how you validated it.

## Review guidelines
- Treat security, secrets, and unsafe execution paths as highest priority.
- Never add or log credentials, tokens, or personal data.
- Prefer deterministic behavior and reproducible installs (pin versions when adding deps).
- If behavior changes, update README/docs and add/adjust a test when tests exist.
- Flag documentation typos only if they materially affect understanding.

## Repo hygiene
- Do not commit large datasets; add to `.gitignore` and document how to obtain data.
- Prefer small examples / fixtures under a `examples/` or `tests/fixtures/` folder.
