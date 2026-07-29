"""
LangGraph StateGraph definition for the Job Application Agent.

Flow:
  START → fetch_jd → parse_jd → score_profiles → analyse_gaps → update_ats → END
"""

from state import JobAgentState
from langgraph.graph import StateGraph, START, END

from .nodes import (
    fetch_jd_node,
    parse_jd_node,
    score_profiles_node,
    analyse_gaps_node,
    update_ats_node,
)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_graph():
    """Build and compile the LangGraph job agent workflow."""

    builder = StateGraph(JobAgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("fetch_jd",       fetch_jd_node)
    builder.add_node("parse_jd",       parse_jd_node)
    builder.add_node("score_profiles", score_profiles_node)
    builder.add_node("analyse_gaps",   analyse_gaps_node)
    builder.add_node("update_ats",     update_ats_node)

    # ── Wire edges (linear pipeline) ─────────────────────────────────────────
    builder.add_edge(START,            "fetch_jd")
    builder.add_edge("fetch_jd",       "parse_jd")
    builder.add_edge("parse_jd",       "score_profiles")
    builder.add_edge("score_profiles", "analyse_gaps")
    builder.add_edge("analyse_gaps",   "update_ats")
    builder.add_edge("update_ats",     END)

    return builder.compile()


# Singleton — import `graph` directly from this module
graph = create_graph()
