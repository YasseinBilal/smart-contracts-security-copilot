import re

from app.detectors.base import Detector, StaticFinding

_DELEGATECALL = re.compile(r"\bdelegatecall\s*\(", re.IGNORECASE)
# Dangerous patterns: delegatecall to a user-supplied or state-variable address
_USER_SUPPLIED = re.compile(
    r"delegatecall\s*\(\s*(abi\.encodeWithSelector|abi\.encodeWithSignature|"
    r"abi\.encode)\s*\(",
    re.IGNORECASE,
)
_HARDCODED = re.compile(r"delegatecall\s*\(\s*0x[0-9a-fA-F]{40}", re.IGNORECASE)


class DelegatecallDetector(Detector):
    """Detects dangerous delegatecall patterns."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        for i, line in enumerate(lines, start=1):
            if not _DELEGATECALL.search(line):
                continue

            # Skip if it's a hardcoded address (lower risk — still flag but lower severity)
            if _HARDCODED.search(line):
                findings.append(
                    StaticFinding(
                        category="DELEGATECALL",
                        severity="MEDIUM",
                        title="delegatecall to hardcoded address",
                        description=(
                            f"Line {i}: `delegatecall` to a hardcoded address. "
                            "If the target contract's storage layout differs from this "
                            "contract's, storage corruption will occur. Verify storage "
                            "layout compatibility."
                        ),
                        affected_lines=[i],
                        affected_code=line.strip(),
                        confidence="MEDIUM",
                        filename=filename,
                    )
                )
                continue

            # Look 3 lines back for the target address (often set in a variable)
            context_lines = lines[max(0, i - 4) : i]
            context_text = " ".join(context_lines)

            if re.search(r"(msg\.data|_impl|implementation|target|_target)", context_text, re.IGNORECASE):
                findings.append(
                    StaticFinding(
                        category="DELEGATECALL",
                        severity="CRITICAL",
                        title="delegatecall to potentially user-controlled address",
                        description=(
                            f"Line {i}: `delegatecall` target may be user-controlled or from "
                            "a mutable implementation variable. An attacker could point this "
                            "to a malicious contract that executes arbitrary code in this "
                            "contract's storage context. Storage layout must be identical. "
                            "Real example: Parity Multisig ($150M frozen, 2017)."
                        ),
                        affected_lines=[i],
                        affected_code=line.strip(),
                        confidence="MEDIUM",
                        filename=filename,
                    )
                )

        return findings
