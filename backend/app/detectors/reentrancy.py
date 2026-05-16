import re

from app.detectors.base import Detector, StaticFinding

# Patterns for external calls that send ETH or call external contracts
_EXTERNAL_CALL = re.compile(
    r"\.(call\s*\{[^}]*value\s*:|\bcall\b\s*\()", re.IGNORECASE
)
_TRANSFER_SEND = re.compile(r"\.(transfer|send)\s*\(", re.IGNORECASE)
# State variable write patterns (balance/amount assignments, mappings)
_STATE_WRITE = re.compile(
    r"(balances|balance|amounts|amount|deposits|deposit)\s*\[.*\]\s*[-+]?=(?!=)",
    re.IGNORECASE,
)
# Guard patterns that indicate reentrancy protection
_NONREENTRANT = re.compile(r"\bnonReentrant\b|\bReentrancyGuard\b")

_FUNCTION_START = re.compile(r"\bfunction\s+\w+")


class ReentrancyDetector(Detector):
    """Detects CEI (Checks-Effects-Interactions) violations in Solidity functions."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        # Skip if contract uses ReentrancyGuard broadly
        full_source_protected = bool(_NONREENTRANT.search(source))

        functions = self._split_into_functions(lines)

        for func_name, func_lines, start_lineno in functions:
            func_text = "\n".join(func_lines)

            # Skip if this individual function has nonReentrant modifier
            if full_source_protected or _NONREENTRANT.search(func_text):
                continue

            # Find external call lines and state write lines within function
            call_linenos = []
            write_linenos = []
            for i, line in enumerate(func_lines):
                abs_lineno = start_lineno + i
                if _EXTERNAL_CALL.search(line) or _TRANSFER_SEND.search(line):
                    call_linenos.append(abs_lineno)
                if _STATE_WRITE.search(line):
                    write_linenos.append(abs_lineno)

            # CEI violation: external call appears BEFORE a state write
            for call_line in call_linenos:
                for write_line in write_linenos:
                    if call_line < write_line:
                        affected = list(range(call_line, write_line + 1))
                        code_snippet = "\n".join(
                            lines[call_line - 1 : write_line]
                        )
                        findings.append(
                            StaticFinding(
                                category="REENTRANCY",
                                severity="CRITICAL",
                                title=f"Reentrancy: CEI violation in {func_name}()",
                                description=(
                                    f"Function `{func_name}` performs an external call "
                                    f"at line {call_line} before updating state at line {write_line}. "
                                    "This violates the Checks-Effects-Interactions pattern and "
                                    "allows a reentrancy attack where the attacker re-enters before "
                                    "the balance is updated."
                                ),
                                affected_lines=affected,
                                affected_code=code_snippet,
                                confidence="HIGH",
                                filename=filename,
                            )
                        )
                        break  # one finding per function is enough

        return findings

    def _split_into_functions(
        self, lines: list[str]
    ) -> list[tuple[str, list[str], int]]:
        """Split source into (func_name, lines, start_lineno) tuples."""
        functions = []
        current_func: list[str] = []
        current_name = "unknown"
        current_start = 1
        depth = 0
        in_func = False

        for i, line in enumerate(lines, start=1):
            m = _FUNCTION_START.search(line)
            if m and not in_func:
                current_name = re.search(r"function\s+(\w+)", line).group(1)  # type: ignore[union-attr]
                current_start = i
                in_func = True
                current_func = [line]
                depth = line.count("{") - line.count("}")
                continue

            if in_func:
                current_func.append(line)
                depth += line.count("{") - line.count("}")
                if depth <= 0:
                    functions.append((current_name, current_func, current_start))
                    in_func = False
                    current_func = []

        return functions
