"""NexaAI LangGraph Builder — Stateful Directed Agent Graph."""
from langgraph.graph import StateGraph, START, END
from app.graph.nodes import (
    agent_reasoner_node,
    input_guardrail_node,
    intent_analyzer_node,
    output_guardrail_node,
    refusal_handler_node,
)
from app.graph.state import NexaGraphState


def route_guardrail_decision(state: NexaGraphState) -> str:
    """Conditional router based on input guardrail safety analysis."""
    if state.get("safety_flagged", False):
        return "refusal_handler"
    return "intent_analyzer"


def build_nexa_graph() -> StateGraph:
    """Constructs the multi-node state graph for NexaAI assistant."""
    workflow = StateGraph(NexaGraphState)

    # Register graph nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("intent_analyzer", intent_analyzer_node)
    workflow.add_node("refusal_handler", refusal_handler_node)
    workflow.add_node("agent_reasoner", agent_reasoner_node)
    workflow.add_node("output_guardrail", output_guardrail_node)

    # Graph edge topology
    workflow.add_edge(START, "input_guardrail")
    workflow.add_conditional_edges(
        "input_guardrail",
        route_guardrail_decision,
        {
            "refusal_handler": "refusal_handler",
            "intent_analyzer": "intent_analyzer",
        },
    )
    workflow.add_edge("intent_analyzer", "agent_reasoner")
    workflow.add_edge("agent_reasoner", "output_guardrail")
    workflow.add_edge("refusal_handler", "output_guardrail")
    workflow.add_edge("output_guardrail", END)

    return workflow


def compile_nexa_graph():
    """Compiles the state graph into an executable runnable."""
    return build_nexa_graph().compile()
