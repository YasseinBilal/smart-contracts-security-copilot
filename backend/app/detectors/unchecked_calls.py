import re

from app.detectors.base import Detector, StaticFinding

# .call() that returns (bool, bytes) — we look for calls where return value is ignored
_RAW_CALL = re.compile(r"\.(call|delegatecall|staticcall)\s*\{?[^;]*\}", re.IGNORECASE)
_CALL_WITH_ASSIGNMENT = re.compile(
    r"(bool\s+\w+\s*,|,?\s*bytes\s+\w+|\(bool|bool\s+success)",
    re.IGNORECASE,
)
# Low-level send (deprecated but still used)
_SEND = re.compile(r"\.(send)\s*\(", re.IGNORECASE)
_SEND_CHECKED = re.compile(r"require\s*\(.*\.send\s*\(|bool.*\.send\s*\(", re.IGNORECASE)


class UncheckedCallsDetector(Detector):
    """Detects low-level calls whose return value is not checked."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        for i, line in enumerate(lines, start=1):
            # Check for .send() without return value check
            if _SEND.search(line) and not _SEND_CHECKED.search(line):
                # Verify it's not inside a require or assignment
                if "require" not in line and "bool " not in line:
                    findings.append(
                        StaticFinding(
                            category="UNCHECKED_CALLS",
                            severity="MEDIUM",
                            title="Unchecked .send() return value",
                            description=(
                                f"Line {i}: `.send()` returns a bool indicating success/failure. "
                                "Ignoring this return value means failed transfers are silently "
                                "swallowed. Use `.call{{value:}}()` and check the bool return."
                            ),
                            affected_lines=[i],
                            affected_code=line.strip(),
                            confidence="HIGH",
                            filename=filename,
                        )
                    )

            # Check for .call() without checking bool return
            if _RAW_CALL.search(line):
                if not _CALL_WITH_ASSIGNMENT.search(line):
                    # Look at surrounding context: previous/next line for bool assignment
                    prev = lines[i - 2] if i >= 2 else ""
                    nxt = lines[i] if i < len(lines) else ""
                    if not _CALL_WITH_ASSIGNMENT.search(prev + nxt):
                        findings.append(
                            StaticFinding(
                                category="UNCHECKED_CALLS",
                                severity="MEDIUM",
                                title="Unchecked low-level call return value",
                                description=(
                                    f"Line {i}: Low-level `.call()` return value not captured. "
                                    "Failed calls proceed silently. Always: "
                                    "`(bool success, ) = addr.call{{value: v}}(\"\"); require(success);`"
                                ),
                                affected_lines=[i],
                                affected_code=line.strip(),
                                confidence="MEDIUM",
                                filename=filename,
                            )
                        )

        return findings
