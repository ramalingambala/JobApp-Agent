"""LangGraph state definition for the Job Application Agent."""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class JobAgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────────
    job_url: str                          # LinkedIn / Glassdoor / any job URL
    search_query: Optional[str]           # fallback: search by query string
    # LinkedIn/Glassdoor/Indeed/Naukri/Any
    portal: Optional[str]
    skip_cover: Optional[bool]            # skip cover letter (bulk/fast mode)

    # ── JD Processing ─────────────────────────────────────────────────────────
    raw_jd: str                           # raw fetched text
    # structured: title, company, requirements
    parsed_jd: Optional[dict]
    # exact posting URL from Exa search result
    job_source_url: Optional[str]

    # ── Profile Scoring ───────────────────────────────────────────────────────
    ic_score: Optional[float]
    leadership_score: Optional[float]
    best_profile: Optional[str]           # "IC" | "Leadership"
    strengths: Optional[list]
    gaps: Optional[list]
    levers: Optional[list]                # actionable improvement strings

    # ── Output ────────────────────────────────────────────────────────────────
    cover_letter: Optional[str]
    ats_entry: Optional[str]              # formatted line for ATS-Scores.md

    # ── Agent messages (LangGraph built-in reducer) ───────────────────────────
    messages: Annotated[list, add_messages]
