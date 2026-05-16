import json
from app.detectors.base import StaticFinding
from app.memory.vector_search import SimilarVuln


def build_analysis_prompt(
    source: str,
    filename: str,
    static_findings: list[StaticFinding],
    rag_context: list[SimilarVuln],
) -> str:
    rag_section = ""
    if rag_context:
        rag_entries = "\n\n".join(
            f"[{v.category or 'GENERAL'}] {v.content[:500]}" for v in rag_context
        )
        rag_section = f"""
## Relevant Historical Exploit Context
The following known vulnerability patterns are semantically similar to what was detected.
Use this context to calibrate severity and enrich your analysis:

{rag_entries}
"""

    static_section = (
        json.dumps(
            [
                {
                    "finding_id": f.finding_id,
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "affected_lines": f.affected_lines,
                    "affected_code": f.affected_code,
                    "confidence": f.confidence,
                }
                for f in static_findings
            ],
            indent=2,
        )
        if static_findings
        else "[]"
    )

    return f"""
## Contract Under Review: {filename}

```solidity
{source[:8000]}
```
{rag_section}
## Static Analysis Pre-Findings
These patterns were detected deterministically. Your tasks:
1. Confirm or mark false_positive=true for each finding
2. Enrich each confirmed finding with exploit_scenario and recommendation
3. Add any CRITICAL/HIGH findings the static pass missed (business logic flaws, invariant violations)
4. Calibrate severity using Sherlock's framework

Pre-findings:
{static_section}

## Required JSON Output Schema
{{
  "findings": [
    {{
      "finding_id": "string (keep from static, or generate new UUID for new findings)",
      "category": "REENTRANCY|ACCESS_CONTROL|INTEGER_OVERFLOW|UNCHECKED_CALLS|ORACLE_MANIPULATION|SIGNATURE_REPLAY|FLASH_LOAN|FRONT_RUNNING|DELEGATECALL|LOGIC_FLAW",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "title": "string (concise, e.g. 'Reentrancy in withdraw()')",
      "description": "string (2-3 sentences explaining the vulnerability)",
      "affected_lines": [integer],
      "affected_code": "string (the vulnerable code snippet)",
      "recommendation": "string (specific, actionable fix)",
      "exploit_scenario": "string (step-by-step attack narrative)",
      "confidence": "HIGH|MEDIUM|LOW",
      "false_positive": false
    }}
  ],
  "summary": {{
    "critical": integer,
    "high": integer,
    "medium": integer,
    "low": integer,
    "info": integer,
    "notes": "string (overall contract security assessment)"
  }}
}}
""".strip()
