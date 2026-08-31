"""Deterministic local terminology resolution for academic translation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class GlossaryValidationError(ValueError):
    """Raised when a glossary cannot be applied deterministically."""


@dataclass(frozen=True)
class GlossaryEntry:
    identifier: str
    source: str
    target: str
    policy: str
    case_sensitive: bool
    category: str


@dataclass(frozen=True)
class GlossaryMatch:
    entry: GlossaryEntry
    start: int
    end: int


def _entry(value: Any) -> GlossaryEntry:
    if not isinstance(value, dict):
        raise GlossaryValidationError("glossary entry must be an object")
    required = ("id", "source", "target", "policy", "case_sensitive", "category")
    if any(not isinstance(value.get(field), str) or not value[field].strip() for field in required if field != "case_sensitive"):
        raise GlossaryValidationError("glossary entry has missing string fields")
    if not isinstance(value.get("case_sensitive"), bool):
        raise GlossaryValidationError("case_sensitive must be a boolean")
    if value["policy"] not in {"translate", "preserve"}:
        raise GlossaryValidationError(f"unsupported glossary policy: {value['policy']!r}")
    return GlossaryEntry(value["id"], value["source"], value["target"], value["policy"], value["case_sensitive"], value["category"])


class GlossaryResolver:
    def __init__(self, entries: Iterable[GlossaryEntry]) -> None:
        self.entries = tuple(entries)
        if not self.entries:
            raise GlossaryValidationError("glossary must contain entries")
        if len({entry.identifier for entry in self.entries}) != len(self.entries):
            raise GlossaryValidationError("glossary entry ids must be unique")
        seen: dict[tuple[str, bool], GlossaryEntry] = {}
        for entry in self.entries:
            key = (entry.source if entry.case_sensitive else entry.source.casefold(), entry.case_sensitive)
            other = seen.get(key)
            if other and (other.target, other.policy) != (entry.target, entry.policy):
                raise GlossaryValidationError(f"conflicting glossary entries for {entry.source!r}")
            seen[key] = entry
        self._ordered = tuple(sorted(self.entries, key=lambda entry: len(entry.source), reverse=True))

    def matches(self, text: str) -> list[GlossaryMatch]:
        occupied = [False] * len(text)
        found: list[GlossaryMatch] = []
        for entry in self._ordered:
            flags = 0 if entry.case_sensitive else re.IGNORECASE
            pattern = re.compile(r"(?<!\w)" + re.escape(entry.source) + r"(?!\w)", flags)
            for match in pattern.finditer(text):
                if any(occupied[match.start():match.end()]):
                    continue
                occupied[match.start():match.end()] = [True] * (match.end() - match.start())
                found.append(GlossaryMatch(entry, match.start(), match.end()))
        return sorted(found, key=lambda match: match.start)

    def apply(self, text: str) -> str:
        result = text
        for match in reversed(self.matches(text)):
            result = result[:match.start] + match.entry.target + result[match.end:]
        return result


def load_glossary(path: str | Path) -> GlossaryResolver:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise GlossaryValidationError("unsupported glossary schema")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise GlossaryValidationError("glossary entries must be a list")
    return GlossaryResolver(_entry(value) for value in entries)
