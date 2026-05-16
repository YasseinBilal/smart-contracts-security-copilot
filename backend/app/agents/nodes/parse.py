import json
import subprocess
import tempfile
import time
from pathlib import Path

from app.agents.state import AuditState


async def parse_node(state: AuditState) -> AuditState:
    t0 = time.monotonic()
    source = state["source"]
    filename = state.get("filename", "contract.sol")

    ast: dict = {}
    error: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".sol", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmppath = f.name

        result = subprocess.run(
            ["slither", tmppath, "--print", "contract-summary", "--json", "-"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            try:
                ast = json.loads(result.stdout)
            except json.JSONDecodeError:
                ast = {"raw": result.stdout[:2000]}
        else:
            # Fallback: basic line-based AST info
            ast = _basic_ast(source)
            if result.stderr:
                error = result.stderr[:500]

        Path(tmppath).unlink(missing_ok=True)
    except FileNotFoundError:
        # Slither not installed — use basic AST
        ast = _basic_ast(source)
        error = "Slither not available; using basic AST parsing"
    except subprocess.TimeoutExpired:
        ast = _basic_ast(source)
        error = "Slither timed out; using basic AST parsing"
    except Exception as e:
        ast = _basic_ast(source)
        error = str(e)

    return {
        **state,
        "ast": ast,
        "parse_error": error,
        "parse_latency": time.monotonic() - t0,
    }


def _basic_ast(source: str) -> dict:
    """Minimal AST extraction without Slither."""
    import re

    functions = re.findall(r"\bfunction\s+(\w+)\s*\(", source)
    contracts = re.findall(r"\bcontract\s+(\w+)", source)
    imports = re.findall(r'^import\s+["\']([^"\']+)["\']', source, re.MULTILINE)

    return {
        "contracts": contracts,
        "functions": functions,
        "imports": imports,
        "line_count": len(source.splitlines()),
    }
