import re

from app.detectors.base import Detector, StaticFinding

_GET_RESERVES = re.compile(r"\bgetReserves\s*\(", re.IGNORECASE)
_TWAP_PATTERN = re.compile(
    r"(blockTimestampLast|price0CumulativeLast|price1CumulativeLast|"
    r"TWAP|twap|TimeWeighted|timeWeighted|observe\s*\(|consult\s*\()",
    re.IGNORECASE,
)
_SPOT_PRICE_CALC = re.compile(r"reserve\d\s*/\s*reserve\d", re.IGNORECASE)
_CHAINLINK = re.compile(r"(latestRoundData|latestAnswer|AggregatorV3Interface)", re.IGNORECASE)


class OracleManipulationDetector(Detector):
    """Detects reliance on spot price from AMM without TWAP protection."""

    def detect(self, source: str, filename: str = "") -> list[StaticFinding]:
        findings = []
        lines = source.splitlines()

        uses_twap = bool(_TWAP_PATTERN.search(source))
        uses_chainlink = bool(_CHAINLINK.search(source))

        if uses_twap or uses_chainlink:
            return findings

        for i, line in enumerate(lines, start=1):
            if _GET_RESERVES.search(line) or _SPOT_PRICE_CALC.search(line):
                findings.append(
                    StaticFinding(
                        category="ORACLE_MANIPULATION",
                        severity="HIGH",
                        title="Spot price oracle manipulation risk",
                        description=(
                            f"Line {i}: Contract reads spot price via `getReserves()` from a "
                            "Uniswap V2 pair (or computes reserve ratio directly) without using "
                            "TWAP. Spot prices can be manipulated within a single transaction "
                            "using a flash loan. This enables price manipulation attacks. "
                            "Real examples: bZx ($1M, 2020), Cream Finance ($130M, 2021)."
                        ),
                        affected_lines=[i],
                        affected_code=line.strip(),
                        confidence="HIGH",
                        filename=filename,
                    )
                )
                break  # one finding per contract is enough

        return findings
