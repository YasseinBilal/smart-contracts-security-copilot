from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal
import hashlib
import re

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
VulnCategory = Literal[
    "REENTRANCY",
    "ACCESS_CONTROL",
    "INTEGER_OVERFLOW",
    "UNCHECKED_CALLS",
    "ORACLE_MANIPULATION",
    "SIGNATURE_REPLAY",
    "FLASH_LOAN",
    "FRONT_RUNNING",
    "DELEGATECALL",
]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass
class StaticFinding:
    category: VulnCategory
    severity: Severity
    title: str
    description: str
    affected_lines: list[int]
    affected_code: str
    confidence: Confidence
    filename: str = ""
    finding_id: str = field(default="")

    def __post_init__(self):
        if not self.finding_id:
            key = f"{self.filename}:{self.category}:{sorted(self.affected_lines)}"
            self.finding_id = hashlib.sha256(key.encode()).hexdigest()[:12]


class Detector(ABC):
    @abstractmethod
    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        """Run detection on raw Solidity source. Returns list of findings."""

    def _extract_lines(self, source: str, pattern: re.Pattern) -> list[tuple[int, str]]:
        """Return (line_number, line_text) for each line matching pattern."""
        results = []
        for i, line in enumerate(source.splitlines(), start=1):
            if pattern.search(line):
                results.append((i, line))
        return results

    def _get_surrounding_lines(self, source: str, line_num: int, context: int = 3) -> str:
        lines = source.splitlines()
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        return "\n".join(lines[start:end])
