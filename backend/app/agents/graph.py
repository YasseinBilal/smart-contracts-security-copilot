from langgraph.graph import StateGraph, END

from app.agents.state import AuditState
from app.agents.nodes.parse import parse_node
from app.agents.nodes.static_scan import static_scan_node
from app.agents.nodes.memory_query import memory_query_node
from app.agents.nodes.ai_reason import ai_reason_node
from app.agents.nodes.test_gen import test_gen_node
from app.agents.nodes.explain import explain_node
from app.agents.nodes.report import report_node


def build_audit_graph() -> StateGraph:
    graph = StateGraph(AuditState)

    graph.add_node("parse", parse_node)
    graph.add_node("static_scan", static_scan_node)
    graph.add_node("memory_query", memory_query_node)
    graph.add_node("ai_reason", ai_reason_node)
    graph.add_node("test_gen", test_gen_node)
    graph.add_node("explain", explain_node)
    graph.add_node("report", report_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse", "static_scan")
    graph.add_edge("static_scan", "memory_query")
    graph.add_edge("memory_query", "ai_reason")
    graph.add_edge("ai_reason", "test_gen")
    graph.add_edge("test_gen", "explain")
    graph.add_edge("explain", "report")
    graph.add_edge("report", END)

    return graph


audit_workflow = build_audit_graph().compile()
