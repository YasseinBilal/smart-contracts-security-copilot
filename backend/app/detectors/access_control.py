import re

from app.detectors.base import Detector, StaticFinding

# Functions with privileged names that should require access control
_PRIVILEGED_NAMES = re.compile(
    r"\bfunction\s+(mint|burn|pause|unpause|initialize|setOwner|transferOwnership|"
    r"upgrade|upgradeTo|withdraw|withdrawAll|setFee|setPrice|addAdmin|removeAdmin|"
    r"emergencyWithdraw|drain)\s*\(",
    re.IGNORECASE,
)
# Access control modifiers / checks.
# Word-bounded alternatives (end in word chars) are grouped separately from
# require(msg.sender ==) which ends in '==' and cannot use a trailing \b.
_ACCESS_GUARD = re.compile(
    r"\b(onlyOwner|onlyAdmin|onlyRole|onlyMinter|onlyPauser|onlyGovernance|"
    r"hasRole|_checkOwner|AccessControl)\b"
    r"|require\s*\(\s*msg\.sender\s*=="
    r"|require\s*\(\s*_msgSender\s*\(\s*\)\s*==",
    re.IGNORECASE,
)
# withdraw/withdrawAll are user-facing when they gate on the caller's own balance.
# emergencyWithdraw and drain are always admin-only (drain the whole vault).
_USER_WITHDRAW_NAMES = re.compile(r"\bfunction\s+(withdraw|withdrawAll)\s*\(", re.IGNORECASE)
# Matches per-caller balance checks: balances[msg.sender], _balances[msg.sender], etc.
_USER_BALANCE_GUARD = re.compile(r"\b\w*[Bb]alances?\s*\[\s*msg\.sender\s*\]", re.IGNORECASE)
_FUNCTION_START = re.compile(r"\bfunction\s+(\w+)")
_VISIBILITY = re.compile(r"\b(public|external)\b")


class AccessControlDetector(Detector):
    """Detects privileged functions missing access control modifiers or guards."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        for i, line in enumerate(lines, start=1):
            m = _PRIVILEGED_NAMES.search(line)
            if not m:
                continue

            func_name_match = _FUNCTION_START.search(line)
            if not func_name_match:
                continue
            func_name = func_name_match.group(1)

            # Only flag public/external functions
            if not _VISIBILITY.search(line):
                continue

            # Collect the full function signature (may span next line)
            func_header = line
            if i < len(lines):
                func_header += " " + lines[i]

            if _ACCESS_GUARD.search(func_header):
                continue

            # Also check the first few lines inside the function body for a require/guard
            body_start = i
            guarded = False
            for j in range(body_start, min(body_start + 5, len(lines))):
                if _ACCESS_GUARD.search(lines[j]):
                    guarded = True
                    break
            if guarded:
                continue

            # withdraw/withdrawAll with a per-caller balance check are user-facing,
            # not privileged admin functions — skip to avoid false positives.
            if _USER_WITHDRAW_NAMES.search(line):
                user_guarded = False
                for j in range(body_start, min(body_start + 10, len(lines))):
                    if _USER_BALANCE_GUARD.search(lines[j]):
                        user_guarded = True
                        break
                if user_guarded:
                    continue

            findings.append(
                StaticFinding(
                    category="ACCESS_CONTROL",
                    severity="HIGH",
                    title=f"Missing access control on {func_name}()",
                    description=(
                        f"The function `{func_name}` is public/external and performs a privileged "
                        "operation but has no visible access control modifier (onlyOwner, onlyRole, "
                        "require(msg.sender == owner), etc.). Any address can call this function."
                    ),
                    affected_lines=[i],
                    affected_code=line.strip(),
                    confidence="MEDIUM",
                    filename=filename,
                )
            )

        return findings
