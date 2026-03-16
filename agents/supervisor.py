"""
Supervisor: LangGraph StateGraph
────────────────────────────────────────────────────────────────────────────
Wires all 5 agents into a directed state graph.
A1 (Harvester) and A2 (Social Monitor) run in parallel via Send API.
"""
import logging
from langgraph.graph import StateGraph, END
from langgraph.constants import Send

from agents.state import SwarmState
from agents.harvester import run_harvester
from agents.social_monitor import run_social_monitor
from agents.auditor import run_auditor
from agents.fact_checker import run_fact_checker
from agents.judge import run_judge

logger = logging.getLogger(__name__)


def route_after_harvest(state: SwarmState):
    """
    After both harvesters have deposited data, proceed to Auditor.
    This node acts as a fan-in join point.
    """
    return "auditor"


def route_after_audit(state: SwarmState):
    """Proceed to Fact-Checker, or skip directly to Judge if no claims."""
    audit_results = state.get("audit_results", [])
    if not audit_results:
        logger.warning("No audit results — skipping Fact-Checker")
        return "judge"
    return "fact_checker"


def route_after_fact_check(state: SwarmState):
    if state.get("error"):
        logger.warning("Error in swarm — routing to Judge for partial report")
    return "judge"


def build_swarm_graph() -> StateGraph:
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(SwarmState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("harvester", run_harvester)
    graph.add_node("social_monitor", run_social_monitor)
    graph.add_node("auditor", run_auditor)
    graph.add_node("fact_checker", run_fact_checker)
    graph.add_node("judge", run_judge)

    # ── Fan-out: Start → [Harvester, Social Monitor] in parallel ─────────────
    def fan_out(state: SwarmState):
        """Route to both A1 and A2 simultaneously via Send."""
        sends = [Send("harvester", state)]
        if state.get("company_url"):
            sends.append(Send("social_monitor", state))
        return sends

    graph.set_conditional_entry_point(fan_out, path_map={
        "harvester": "harvester",
        "social_monitor": "social_monitor",
    })

    # ── Fan-in: Both harvesters must complete before Auditor ─────────────────
    # LangGraph Annotated[List, operator.add] handles the merge automatically.
    graph.add_edge("harvester", "auditor")
    graph.add_edge("social_monitor", "auditor")

    # ── Linear pipeline after fan-in ─────────────────────────────────────────
    graph.add_conditional_edges("auditor", route_after_audit, {
        "fact_checker": "fact_checker",
        "judge": "judge",
    })
    graph.add_conditional_edges("fact_checker", route_after_fact_check, {
        "judge": "judge",
    })
    graph.add_edge("judge", END)

    return graph.compile()


# Module-level singleton
_swarm_graph = None


def get_swarm() -> StateGraph:
    global _swarm_graph
    if _swarm_graph is None:
        _swarm_graph = build_swarm_graph()
    return _swarm_graph
