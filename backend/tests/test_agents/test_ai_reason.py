import pytest
from unittest.mock import AsyncMock, patch

STATIC_FINDING = {
    "finding_id": "abc123",
    "category": "REENTRANCY",
    "severity": "CRITICAL",
    "title": "Reentrancy in withdraw()",
    "description": "CEI violation — external call before state update.",
    "affected_lines": [9, 10, 11],
    "affected_code": "msg.sender.call{value: bal}",
    "confidence": "HIGH",
    "filename": "VulnBank.sol",
}

MOCK_AI_RESPONSE = {
    "findings": [
        {
            "finding_id": "abc123",
            "category": "REENTRANCY",
            "severity": "CRITICAL",
            "title": "Reentrancy in withdraw()",
            "description": "The withdraw function sends ETH before zeroing the balance.",
            "affected_lines": [9, 10, 11],
            "affected_code": "msg.sender.call{value: bal}",
            "recommendation": "Apply CEI: zero balance before the external call.",
            "exploit_scenario": "Attacker re-enters withdraw() in the fallback function.",
            "confidence": "HIGH",
            "false_positive": False,
        }
    ],
    "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0, "notes": ""},
}


async def test_ai_reason_enriches_findings():
    from app.agents.nodes.ai_reason import ai_reason_node

    state = {
        "source": "contract VulnBank { ... }",
        "filename": "VulnBank.sol",
        "scan_id": "test",
        "static_findings": [STATIC_FINDING],
        "rag_context": [],
    }

    with patch("app.agents.nodes.ai_reason.chat_json", new=AsyncMock(return_value=(MOCK_AI_RESPONSE, 100))):
        result = await ai_reason_node(state)

    assert "ai_findings" in result
    assert len(result["ai_findings"]) == 1
    assert result["ai_findings"][0]["category"] == "REENTRANCY"
    assert result["total_tokens"] == 100


async def test_ai_reason_filters_false_positives():
    from app.agents.nodes.ai_reason import ai_reason_node

    fp_response = {
        "findings": [
            {**MOCK_AI_RESPONSE["findings"][0], "false_positive": True}
        ],
        "summary": {},
    }

    state = {
        "source": "contract X {}",
        "filename": "X.sol",
        "scan_id": "test",
        "static_findings": [STATIC_FINDING],
        "rag_context": [],
    }

    with patch("app.agents.nodes.ai_reason.chat_json", new=AsyncMock(return_value=(fp_response, 50))):
        result = await ai_reason_node(state)

    assert result["ai_findings"] == []


async def test_ai_reason_handles_empty_static_findings():
    from app.agents.nodes.ai_reason import ai_reason_node

    empty_response = {"findings": [], "summary": {}}
    state = {
        "source": "contract X {}",
        "filename": "X.sol",
        "scan_id": "test",
        "static_findings": [],
        "rag_context": [],
    }

    with patch("app.agents.nodes.ai_reason.chat_json", new=AsyncMock(return_value=(empty_response, 20))):
        result = await ai_reason_node(state)

    assert result["ai_findings"] == []
    assert result["total_tokens"] == 20


async def test_ai_reason_accumulates_tokens():
    from app.agents.nodes.ai_reason import ai_reason_node

    state = {
        "source": "contract X {}",
        "filename": "X.sol",
        "scan_id": "test",
        "static_findings": [STATIC_FINDING],
        "rag_context": [],
        "total_tokens": 500,  # already spent in earlier nodes
    }

    with patch("app.agents.nodes.ai_reason.chat_json", new=AsyncMock(return_value=(MOCK_AI_RESPONSE, 200))):
        result = await ai_reason_node(state)

    assert result["total_tokens"] == 700
