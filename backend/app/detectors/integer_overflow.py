import re

from app.detectors.base import Detector, StaticFinding

_OLD_PRAGMA = re.compile(r"pragma\s+solidity\s+(\^?0\.[0-7]\.|>=?\s*0\.[0-7]\.)")
_UNCHECKED_BLOCK = re.compile(r"\bunchecked\s*\{")
_ARITHMETIC = re.compile(r"[+\-*]\s*=|[+\-*]\s+\w")
_SAFE_MATH = re.compile(r"SafeMath|using\s+SafeMath")


class IntegerOverflowDetector(Detector):
    """Detects potential integer overflow in pre-0.8 Solidity or in unchecked blocks."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        is_old_pragma = bool(_OLD_PRAGMA.search(source))
        uses_safe_math = bool(_SAFE_MATH.search(source))

        if is_old_pragma and not uses_safe_math:
            # Flag the pragma line
            for i, line in enumerate(lines, start=1):
                if _OLD_PRAGMA.search(line):
                    findings.append(
                        StaticFinding(
                            category="INTEGER_OVERFLOW",
                            severity="HIGH",
                            title="Integer overflow risk: Solidity <0.8 without SafeMath",
                            description=(
                                "This contract uses a Solidity version below 0.8.0 and does not "
                                "import SafeMath. Arithmetic operations can overflow/underflow "
                                "silently. Example: uint256(0) - 1 = 2^256 - 1."
                            ),
                            affected_lines=[i],
                            affected_code=line.strip(),
                            confidence="HIGH",
                            filename=filename,
                        )
                    )
                    break

        # Flag unchecked blocks (in 0.8+) that contain arithmetic
        in_unchecked = False
        unchecked_start = 0
        depth = 0
        for i, line in enumerate(lines, start=1):
            if _UNCHECKED_BLOCK.search(line):
                in_unchecked = True
                unchecked_start = i
                depth = 1
                continue
            if in_unchecked:
                depth += line.count("{") - line.count("}")
                if _ARITHMETIC.search(line):
                    findings.append(
                        StaticFinding(
                            category="INTEGER_OVERFLOW",
                            severity="MEDIUM",
                            title="Arithmetic in unchecked block",
                            description=(
                                f"Arithmetic operation at line {i} is inside an `unchecked` block "
                                "(starting at line {unchecked_start}). Overflow checks are "
                                "disabled here. Verify this is intentional and safe."
                            ),
                            affected_lines=[unchecked_start, i],
                            affected_code=line.strip(),
                            confidence="MEDIUM",
                            filename=filename,
                        )
                    )
                if depth <= 0:
                    in_unchecked = False

        return findings
