def build_explain_prompt(source: str, filename: str, finding_titles: list[str]) -> str:
    findings_section = (
        "Known findings: " + "; ".join(finding_titles) if finding_titles else "No findings yet."
    )

    return f"""
## Contract to Explain: {filename}

```solidity
{source[:6000]}
```

{findings_section}

Provide a plain-English explanation of this contract for a developer who needs to understand
it quickly. Focus on: what it does, who can call what, and what assumptions it makes about
external contracts or actors.

Required JSON output:
{{
  "summary": "string (2-3 paragraphs: purpose, key mechanisms, how value flows)",
  "privileged_functions": ["list of function names that require elevated access"],
  "trust_assumptions": ["list of things the contract assumes are true about external systems"],
  "risk_notes": "string (any architectural concerns not covered by specific findings)"
}}
""".strip()
