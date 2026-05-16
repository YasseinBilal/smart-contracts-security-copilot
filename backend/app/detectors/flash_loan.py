import re

from app.detectors.base import Detector, StaticFinding

_FLASH_LOAN_INTERFACE = re.compile(
    r"(flashLoan|flashBorrow|executeOperation|onFlashLoan|IERC3156|IFlashLoan)",
    re.IGNORECASE,
)
_BALANCE_CHECK = re.compile(
    r"(balanceOf\s*\(address\s*\(this\)|address\s*\(this\)\.balance)",
    re.IGNORECASE,
)
_CALLBACK = re.compile(r"\bcallback\b|\bexecuteOperation\b|\bonFlashLoan\b", re.IGNORECASE)
_CALLER_CHECK = re.compile(
    r"require\s*\(\s*(msg\.sender\s*==|only|authorized)", re.IGNORECASE
)


class FlashLoanDetector(Detector):
    """Detects flash loan callback functions missing caller verification."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        has_flash_loan = bool(_FLASH_LOAN_INTERFACE.search(source))
        if not has_flash_loan:
            return findings

        for i, line in enumerate(lines, start=1):
            if _CALLBACK.search(line) and ("function " in line):
                # Check the first 10 lines of the function body for caller verification
                caller_verified = False
                for j in range(i, min(i + 10, len(lines))):
                    if _CALLER_CHECK.search(lines[j]):
                        caller_verified = True
                        break

                if not caller_verified:
                    findings.append(
                        StaticFinding(
                            category="FLASH_LOAN",
                            severity="CRITICAL",
                            title="Flash loan callback missing caller verification",
                            description=(
                                f"Line {i}: Flash loan callback function lacks `msg.sender` "
                                "verification. Any contract can call this function and trigger "
                                "the callback logic, potentially manipulating contract state "
                                "as if a legitimate flash loan was completed."
                            ),
                            affected_lines=[i],
                            affected_code=line.strip(),
                            confidence="HIGH",
                            filename=filename,
                        )
                    )

        return findings
