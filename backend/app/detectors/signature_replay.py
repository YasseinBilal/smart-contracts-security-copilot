import re

from app.detectors.base import Detector, StaticFinding

_ECRECOVER = re.compile(r"\becrecover\s*\(", re.IGNORECASE)
_NONCE_PATTERN = re.compile(
    r"(nonces?\s*\[|nonce\s*\+\+|_useNonce|_nonces|nonce\s*:=|nonce\s*=\s*)",
    re.IGNORECASE,
)
_CHAIN_ID = re.compile(
    r"(block\.chainid|chainId|chain_id|CHAIN_ID|EIP712|_domainSeparatorV4|"
    r"_hashTypedDataV4)",
    re.IGNORECASE,
)


class SignatureReplayDetector(Detector):
    """Detects ecrecover usage without nonce tracking or chainId binding."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        has_nonce = bool(_NONCE_PATTERN.search(source))
        has_chain_id = bool(_CHAIN_ID.search(source))

        if has_nonce and has_chain_id:
            return findings

        for i, line in enumerate(lines, start=1):
            if _ECRECOVER.search(line):
                issues = []
                if not has_nonce:
                    issues.append("no per-address nonce tracking (replay within same chain)")
                if not has_chain_id:
                    issues.append("no chainId in signed data (cross-chain replay attack)")

                if issues:
                    findings.append(
                        StaticFinding(
                            category="SIGNATURE_REPLAY",
                            severity="HIGH",
                            title="Signature replay vulnerability",
                            description=(
                                f"Line {i}: `ecrecover` is used but the signature scheme is "
                                f"missing: {'; '.join(issues)}. Valid signed messages can be "
                                "replayed by anyone who observed them. "
                                "Real example: Poly Network ($611M, 2021)."
                            ),
                            affected_lines=[i],
                            affected_code=line.strip(),
                            confidence="HIGH" if not has_nonce else "MEDIUM",
                            filename=filename,
                        )
                    )
                break

        return findings
