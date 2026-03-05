"""Anonymization utilities with stable persona tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from data_swarm import yaml_compat as yaml
from data_swarm.tools.io import UserIO

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


@dataclass
class Anonymizer:
    """Stateful anonymizer for a single run."""

    kb_path: Path
    cache: dict[str, str] = field(default_factory=dict)
    proposed_personas: dict[str, dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kb_path.exists():
            payload = yaml.safe_load(self.kb_path.read_text(encoding="utf-8")) or {}
            for persona in payload.get("personas", []):
                token = str(persona.get("persona_token", "")).strip()
                if token:
                    self.cache[token] = token

    def map_email_to_persona_token(self, io: UserIO, email: str) -> str:
        """Map one email identifier to anonymized persona token."""
        if email in self.cache:
            return self.cache[email]
        token = io.ask("Provide persona token for identifier (format: JD | Director | Org | UK): ").strip()
        token = token or "UNK | Unknown | UnknownOrg | Unknown"
        bracketed = f"[{token}]"
        self.cache[email] = bracketed
        self._propose(token)
        return bracketed

    def map_name_to_persona_token(self, io: UserIO, name: str) -> str:
        """Map one name identifier to anonymized persona token."""
        if name in self.cache:
            return self.cache[name]
        token = io.ask(f"Provide persona token for name '{name}' (format: JD | Director | Org | UK): ").strip()
        token = token or "UNK | Unknown | UnknownOrg | Unknown"
        bracketed = f"[{token}]"
        self.cache[name] = bracketed
        self._propose(token)
        return bracketed

    def sanitize_text(self, text: str) -> tuple[str, set[str]]:
        """Sanitize text using known in-memory mappings only."""
        cleaned = text
        used: set[str] = set()
        for key, token in self.cache.items():
            if key and key in cleaned:
                cleaned = cleaned.replace(key, token)
                used.add(token.strip("[]"))
        cleaned = EMAIL_RE.sub("[ANON_EMAIL]", cleaned)
        return cleaned, used

    def collect_from_text(self, text: str, io: UserIO) -> tuple[str, set[str]]:
        """Prompt mapping for any emails found, then sanitize."""
        for email in sorted(set(EMAIL_RE.findall(text))):
            self.map_email_to_persona_token(io, email)
        return self.sanitize_text(text)

    def write_kb_proposal(self, task_dir: Path) -> Path:
        """Write batched KB proposal for this task."""
        path = task_dir / "kb_update_proposal.yaml"
        payload = {"personas": list(self.proposed_personas.values())}
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def apply_proposal(self, io: UserIO) -> bool:
        """Apply proposed personas to KB only with explicit approval."""
        if not self.proposed_personas:
            return False
        approved = io.ask("Apply proposed persona updates to kb/personas.yaml? [y/N]: ").strip().lower() == "y"
        if not approved:
            return False
        payload = yaml.safe_load(self.kb_path.read_text(encoding="utf-8")) if self.kb_path.exists() else {}
        payload = payload or {}
        existing = payload.get("personas", [])
        known = {item.get("persona_token") for item in existing}
        for item in self.proposed_personas.values():
            if item["persona_token"] not in known:
                existing.append(item)
        payload["personas"] = existing
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)
        self.kb_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return True

    def _propose(self, token: str) -> None:
        if token in self.proposed_personas:
            return
        self.proposed_personas[token] = {
            "persona_token": token,
            "tags": [],
            "preferences": [],
            "comms_style": "",
            "decision_rights": [],
            "relationships": [],
        }
