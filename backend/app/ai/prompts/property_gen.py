def build_property_gen_prompt(source: str, finding: dict) -> str:
    return f"""
## Vulnerability Finding
Title: {finding["title"]}
Severity: {finding["severity"]}
Category: {finding["category"]}
Description: {finding["description"]}
Affected Code: {finding.get("affected_code", "")}
Exploit Scenario: {finding.get("exploit_scenario", "")}

## Contract Source
```solidity
{source[:4000]}
```

## Task
Generate a Certora CVL (.spec file) property stub that captures the universal safety
condition this vulnerability violates. This is NOT a one-scenario test — it is a
universally-quantified property checked by the Certora Prover for ALL inputs and states.

Source: https://docs.certora.com/en/latest/docs/user-guide/index.html

---

## Verified CVL Syntax (from Certora docs — use ONLY these constructs)

### 1. methods block — declare which contract functions are envfree (view/pure)
Envfree functions do NOT receive an `env` parameter when called in CVL.
```
methods {{
    function owner() external returns (address) envfree;
    function totalSupply() external returns (uint256) envfree;
    function balanceOf(address) external returns (uint256) envfree;
    function paused() external returns (bool) envfree;
}}
```

### 2. Invariant — boolean condition that must hold in every reachable state
```
invariant name(params)
    boolean_expression
{{ preserved {{ require ...; }} }}   // preserved block is optional
```
Example:
```
invariant balanceLeqSupply(address user)
    balanceOf(user) <= totalSupply();
```

### 3. Rule — property verified for one symbolic transaction
```
rule name(type param, ...) {{
    env e;           // gives access to e.msg.sender, e.msg.value, e.block.timestamp
    uint256 amount;  // declared variables are symbolic (arbitrary)
    require ...;     // restrict to valid pre-states
    contractFunction(e, amount);
    assert boolean_expression, "human-readable failure message";
}}
```

### 4. Parametric rule — verified for EVERY public function automatically
```
rule name(method f) {{
    env e;
    calldataarg args;
    f(e, args);
    assert ...;
}}
```
Filter to specific methods with:
```
rule name(method f) filtered {{ f -> f.selector == sig:withdraw(uint256).selector }} {{
    ...
}}
```

### 5. Ghost variables + Sstore hooks — track aggregated state across all calls
```
ghost mathint sumBalances {{
    init_state axiom sumBalances == 0;
}}
hook Sstore balances[KEY address user] uint256 newVal (uint256 oldVal) {{
    sumBalances = sumBalances + newVal - oldVal;
}}
invariant solvency()
    sumBalances >= 0;
```

### 6. Types (use exactly as shown)
| Type          | When to use                                                         |
|---------------|---------------------------------------------------------------------|
| `mathint`     | All arithmetic in spec — no overflow, no underflow                  |
| `uint256`     | Match Solidity function parameter types for direct calls            |
| `address`     | Ethereum addresses                                                  |
| `bool`        | Booleans                                                            |
| `env`         | First arg to any non-envfree function call (e.msg.sender etc.)      |
| `method`      | Symbolic method variable in parametric rules                        |
| `calldataarg` | Symbolic call data, paired with `method` in parametric rules        |

### 7. Allowed keywords (complete list — do not use any other CVL keywords)
`rule`, `invariant`, `strong invariant`, `methods`, `ghost`, `persistent ghost`,
`hook`, `Sstore`, `Sload`, `CALL`, `axiom`, `init_state`, `env`, `method`,
`calldataarg`, `mathint`, `require`, `assert`, `if`, `requireInvariant`,
`filtered`, `preserved`, `forall`, `exists`,
`sig:funcName(types).selector`, `f.selector`, `f.isView`, `f.isPure`,
`e.msg.sender`, `e.msg.value`, `e.block.timestamp`, `e.block.number`,
`currentContract`, `nativeBalances`, `envfree`, `returns`, `function`, `external`, `internal`,
`@withrevert`, `lastReverted`

### @withrevert and lastReverted
Call a function with `funcName@withrevert(e)` to allow it to revert without aborting the rule.
After the call, `lastReverted` is a built-in boolean: `true` if the call reverted, `false` if it succeeded.
Use this to assert that unauthorized calls MUST revert:
```
require e.msg.sender != owner();
emergencyWithdraw@withrevert(e);
assert lastReverted, "must revert for non-owner";
```

### persistent ghost
Ghosts used inside CALL opcode hooks MUST be declared `persistent`. A regular ghost
gets havoced across external calls; `persistent` survives the call and retains its value.
```
persistent ghost bool externalCallMade;
```

### nativeBalances
Built-in CVL mapping giving the native ETH balance of any address:
`nativeBalances[currentContract]` is the contract's ETH balance — equivalent to
`address(this).balance` in Solidity, with no need for a `getBalance()` envfree wrapper.

### CALL opcode hook
Fires on every EVM CALL instruction (`.call{{value:}}`, `.transfer`, `.send` all compile to CALL).
Use it to detect when the contract makes an external call:
```
hook CALL(uint g, address addr, uint value, uint argsOffset, uint argsLength,
          uint retOffset, uint retLength) uint rc {{
    externalCallMade = true;
}}
```

### if in hook bodies
Standard `if` / `else` control flow is valid inside hook bodies:
```
hook Sstore balances[KEY address a] uint256 newVal (uint256 oldVal) {{
    sumOfBalances = sumOfBalances + newVal - oldVal;
    if (externalCallMade) {{
        balanceWrittenAfterCall = true;
    }}
}}
```

### 8. DO NOT USE — these are hallucinated keywords not in CVL
- `callee` — does not exist in CVL
- `calledContract` — does not exist in CVL
- `havoc` as a statement in rule bodies — havoc is implicit, not a keyword you write
- `unchecked` — Solidity, not CVL
- `msg.sender` (unqualified) — must be `e.msg.sender` inside rules

---

## Category-Specific Patterns

### REENTRANCY
Generate THREE complementary properties using the CALL opcode hook pattern.

---

BUILDING BLOCKS — declare these ghosts and hooks first (declaration order matters):

```
// Persistent: survives across external calls so the CALL hook can set it
persistent ghost bool externalCallMade;
persistent ghost bool balanceWrittenAfterCall;

ghost mathint sumOfBalances {{
    init_state axiom sumOfBalances == 0;
}}

// Fires on every EVM CALL opcode (.call{{value:}}, .transfer, .send all compile to CALL)
hook CALL(uint g, address addr, uint value, uint argsOffset, uint argsLength,
          uint retOffset, uint retLength) uint rc {{
    externalCallMade = true;
}}

// Fires on every write to balances[...]:
//   (a) keeps sumOfBalances in sync for the solvency invariant
//   (b) flags any write that happens AFTER an external call (CEI violation)
hook Sstore balances[KEY address a] uint256 newValue (uint256 oldValue) {{
    sumOfBalances = sumOfBalances + newValue - oldValue;
    if (externalCallMade) {{
        balanceWrittenAfterCall = true;
    }}
}}
```

---

PROPERTY 1 — noReentrancy_CEI (structural: catches the CEI code-ordering violation)

Parametric over ALL public functions. withdraw() violates it; deposit() and others do not.
Starts from a clean transaction (no external call yet, no post-call balance write).
After calling any function f, asserts that balances was never written after a CALL.

```
rule noReentrancy_CEI(method f) {{
    require !externalCallMade;
    require !balanceWrittenAfterCall;

    env e; calldataarg args;
    f(e, args);

    assert !balanceWrittenAfterCall,
        "CEI violated: balances written after an external call -> reentrancy risk.";
}}
```

---

PROPERTY 2 — noReentrancy_withdraw (focused: same check scoped to withdraw only)

```
rule noReentrancy_withdraw() {{
    require !externalCallMade;
    require !balanceWrittenAfterCall;

    env e; uint256 amount;
    withdraw(e, amount);

    assert !balanceWrittenAfterCall,
        "withdraw() updates balance after sending ETH -> reentrancy risk.";
}}
```

Replace `withdraw(e, amount)` with the actual function signature from the source.
If withdraw takes no arguments, use `withdraw(e)`.

---

PROPERTY 3 — solvency invariant (financial: the contract holds enough ETH for all balances)

Uses `nativeBalances[currentContract]` — the built-in CVL ETH balance — instead of a
getBalance() wrapper. A plain `invariant` is sufficient here because the CALL hook
pattern already handles structural CEI detection above.

```
invariant solvency()
    sumOfBalances <= to_mathint(nativeBalances[currentContract]);
```

---

Declaration order in the final .spec file:
1. `persistent ghost` declarations
2. `ghost mathint` declarations
3. `hook CALL` definition
4. `hook Sstore` definition
5. `rule` definitions
6. `invariant` definition

Do NOT use `use builtin rule viewReentrancy` — the CALL hook pattern above is more
precise and covers both read and write reentrancy.

### ACCESS_CONTROL
Choose the template based on what the affected function actually does.
Read the finding title, description, and affected code to decide which case applies.

CASE 1 — fund-draining function (emergencyWithdraw, drain, or any function that sends
ALL contract ETH to the caller without a per-user balance check):
Assert that the specific function REVERTS when called by a non-owner.

DO NOT use a parametric rule over all functions here — a rule asserting
"only owner can reduce balance" also blocks legitimate user `withdraw()` calls (those
are protected by `balances[msg.sender]`, not by ownership). Name the exact function
and use `@withrevert` + `lastReverted` to assert it must revert for non-owners.

```
methods {{
    function owner() external returns (address) envfree;
}}

// emergencyWithdraw must revert for any caller that is not the owner
rule emergencyWithdrawOnlyOwner() {{
    env e;
    require e.msg.sender != owner();
    emergencyWithdraw@withrevert(e);
    assert lastReverted,
        "emergencyWithdraw must revert when called by non-owner";
}}
```

Replace `emergencyWithdraw` with the actual function name from the finding.

CASE 2 — privileged state variable change (setPaused, setOwner, setFee, upgrade, etc.):
Assert that the specific function REVERTS when called by a non-owner.
Use the same `@withrevert` + `lastReverted` pattern as CASE 1 — name the exact
function, declare argument types to match the function signature, require the caller
is not the owner, then assert the call must revert.

```
methods {{
    function owner() external returns (address) envfree;
}}

// setPaused must revert for any caller that is not the owner
rule setPausedOnlyOwner() {{
    env e; bool val;                        // declare one variable per function argument
    require e.msg.sender != owner();
    setPaused@withrevert(e, val);           // replace with actual function name
    assert lastReverted,
        "setPaused must revert when called by non-owner";
}}
```

Replace `setPaused` with the actual function name and adjust argument variables to
match the function's parameter types (bool, uint256, address, etc.).

### INTEGER_OVERFLOW
Invariant on balance vs. total supply.
```
invariant balanceLeqSupply(address user)
    balanceOf(user) <= totalSupply();
```

### SIGNATURE_REPLAY
Nonce must strictly increase after a signature is consumed.
```
rule nonceIncreasesAfterExecution(address user) {{
    env e;
    mathint nonceBefore = nonces(user);
    executeWithSig(e, user);
    assert nonces(user) > nonceBefore,
        "nonce must be incremented after each signed execution";
}}
```

---

## Output Guidelines

### Declaration order — the Prover is order-sensitive, always follow this sequence:
1. `methods {{ }}` block
2. `ghost` declarations
3. `hook` definitions
4. `invariant` and `rule` definitions

### Other rules:
- SCOPE: Generate ONLY properties that directly address the specific vulnerability category
  in the finding above. The contract source may contain OTHER vulnerability classes —
  ignore them completely. Do not add rules or invariants for unrelated issues.
  Example: a REENTRANCY finding must not include an access-control rule, even if the
  contract also has a missing onlyOwner bug.
- Only declare functions in `methods {{ }}` that you actually CALL in a rule or invariant body.
  If a function is only accessed via a hook, do NOT declare it in `methods`.
- Never write `require true;` in a `preserved` block — it is a tautology that does nothing.
  Either omit the `preserved` block entirely or add a meaningful constraint.
- Do not write a `rule` that duplicates what an `invariant` already asserts.
  An invariant holds after every function call, so a filtered rule on one function is redundant.
- Write at most 2 stubs total (one `invariant` + one `rule` if both add new information).
- Add a one-line comment above each stub explaining the safety condition in plain English.
- Use `mathint` for all arithmetic inside the spec.
- Only use keywords from the "Allowed keywords" list — nothing else.
- The output must be pasteable verbatim into a `.spec` file.

Required JSON output:
{{
  "cvl_stub": "string (complete .spec file section, ready to paste)"
}}
""".strip()
