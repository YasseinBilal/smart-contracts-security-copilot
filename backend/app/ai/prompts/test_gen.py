def build_test_gen_prompt(source: str, finding: dict) -> str:
    return f"""
## Vulnerability to Test
Title: {finding["title"]}
Severity: {finding["severity"]}
Category: {finding["category"]}
Description: {finding["description"]}
Exploit Scenario: {finding.get("exploit_scenario", "")}

## Contract Source
```solidity
{source[:4000]}
```

Generate a Foundry test (forge-std) that proves this vulnerability is exploitable.
The test should:
1. Deploy the vulnerable contract
2. Set up the attack scenario (attacker contract, initial state)
3. Execute the attack
4. Assert that the attack succeeded (e.g., drained funds, bypassed access control)

Required JSON output:
{{
  "test_stub": "string (complete Foundry test file in Solidity, ready to compile)"
}}
""".strip()
