"""
graph.py - LangGraph orchestration: Supervisor routing + full pipeline graph.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from state import DCCTState, AgentStep
from agents.supervisor import supervisor_node
from agents.understand import understand_node
from agents.mapping import mapping_node
from agents.teaching_plan import teaching_plan_node
from agents.assessment import assessment_node
from agents.validator import validator_node


# ── Routing function ────────────────────────────────────────────────────────────

def route_next(state: DCCTState) -> str:
    """Determine the next node based on state.next_agent."""
    next_agent = state.get("next_agent", AgentStep.END)
    if next_agent == AgentStep.END or next_agent == "end":
        return END
    return str(next_agent)


# ── Graph builder ───────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Build and compile the DCCT LangGraph pipeline."""

    builder = StateGraph(DCCTState)

    # Register nodes
    builder.add_node(AgentStep.SUPERVISOR, supervisor_node)
    builder.add_node(AgentStep.UNDERSTAND, understand_node)
    builder.add_node(AgentStep.MAPPING, mapping_node)
    builder.add_node(AgentStep.TEACHING_PLAN, teaching_plan_node)
    builder.add_node(AgentStep.ASSESSMENT, assessment_node)
    builder.add_node(AgentStep.VALIDATOR, validator_node)

    # Entry point
    builder.set_entry_point(AgentStep.SUPERVISOR)

    # Supervisor routes to any agent
    builder.add_conditional_edges(
        AgentStep.SUPERVISOR,
        route_next,
        {
            AgentStep.UNDERSTAND: AgentStep.UNDERSTAND,
            AgentStep.MAPPING: AgentStep.MAPPING,
            AgentStep.TEACHING_PLAN: AgentStep.TEACHING_PLAN,
            AgentStep.ASSESSMENT: AgentStep.ASSESSMENT,
            AgentStep.VALIDATOR: AgentStep.VALIDATOR,
            END: END,
        },
    )

    # Each specialist loops back to supervisor for re-routing
    for step in [
        AgentStep.UNDERSTAND,
        AgentStep.MAPPING,
        AgentStep.TEACHING_PLAN,
        AgentStep.ASSESSMENT,
        AgentStep.VALIDATOR,
    ]:
        builder.add_conditional_edges(
            step,
            route_next,
            {
                AgentStep.SUPERVISOR: AgentStep.SUPERVISOR,
                AgentStep.UNDERSTAND: AgentStep.UNDERSTAND,
                AgentStep.MAPPING: AgentStep.MAPPING,
                AgentStep.TEACHING_PLAN: AgentStep.TEACHING_PLAN,
                AgentStep.ASSESSMENT: AgentStep.ASSESSMENT,
                AgentStep.VALIDATOR: AgentStep.VALIDATOR,
                END: END,
            },
        )

    return builder.compile()


# Compiled graph (importable singleton)
graph = build_graph()
