"""LangGraph node functions for the Job Application Agent."""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

load_dotenv()

# ── LLM setup: Groq (primary) + OpenAI GPT-4o-mini (fallback) ────────────────
_llm = None
_fallback_llm = None


def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0,
            max_tokens=4096,
            model_kwargs={"seed": int(os.getenv("GROQ_SEED", "42"))},
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


def get_fallback_llm():
    """Azure OpenAI (or OpenAI) fallback — used automatically when Groq hits rate limits."""
    global _fallback_llm
    if _fallback_llm is None:
        provider = os.getenv("AI_PROVIDER", "openai").lower()
        model = os.getenv("AI_MODEL", "gpt-4o-mini")

        if provider == "azure":
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            api_version = os.getenv(
                "AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
            if not endpoint or not api_key:
                raise RuntimeError(
                    "Groq rate-limited and AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_API_KEY "
                    "are not set. Add them to job-agent/.env to enable the fallback."
                )
            from langchain_openai import AzureChatOpenAI
            _fallback_llm = AzureChatOpenAI(
                azure_deployment=model,
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
                temperature=0,
                max_tokens=4096,
            )
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise RuntimeError(
                    "Groq rate-limited and OPENAI_API_KEY is not set. "
                    "Add it to job-agent/.env to enable the fallback."
                )
            from langchain_openai import ChatOpenAI
            _fallback_llm = ChatOpenAI(
                model=model,
                temperature=0,
                max_tokens=4096,
                api_key=api_key,
            )
    return _fallback_llm


_RATE_LIMIT_SIGNALS = ("rate_limit", "rate limit",
                       "429", "quota", "too many requests")


def _retry_after_seconds(err: Exception) -> float:
    """Extract Groq's suggested wait from a 429 message, e.g. 'try again in 2.79s'."""
    import re
    m = re.search(r"try again in ([\d.]+)\s*s", str(err))
    return float(m.group(1)) if m else 0.0


def _invoke_llm(messages: list, max_retries: int = 5) -> object:
    """Invoke the single pinned Groq model, retrying with backoff on rate limits
    so a TPM spike does not crash the pipeline. Keeps scores deterministic
    (same model + temperature=0). Falls back only if retries are exhausted."""
    import time
    last_err = None
    for attempt in range(max_retries):
        try:
            return get_llm().invoke(messages)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if not any(sig in str(exc).lower() for sig in _RATE_LIMIT_SIGNALS):
                raise
            wait = _retry_after_seconds(exc) or (2.0 ** attempt)
            time.sleep(min(wait + 0.5, 30.0))
    try:
        return get_fallback_llm().invoke(messages)
    except Exception:  # noqa: BLE001
        raise last_err


# ── Node 1: Fetch JD via Exa MCP ─────────────────────────────────────────────

_PORTAL_DOMAINS = {
    "LinkedIn":  ["linkedin.com"],
    "Glassdoor": ["glassdoor.com"],
    "Indeed":    ["indeed.com"],
    "Naukri":    ["naukri.com"],
    "Any":       [],
}


def fetch_jd_node(state: dict) -> dict:
    """
    Fetch job description text from a URL or search query using Exa.
    When a portal is specified (LinkedIn/Glassdoor/Indeed/Naukri), scopes
    the search to that portal's domain and captures the exact posting URL.
    """
    from exa_py import Exa
    import re as _re

    job_url = state.get("job_url", "").strip()
    search_query = state.get("search_query", "").strip()
    portal = state.get("portal", "Any")

    # pasted text already in state — skip fetch entirely
    if state.get("raw_jd", "").strip():
        return {"raw_jd": state["raw_jd"], "job_source_url": state.get("job_source_url", "")}

    exa = Exa(api_key=os.getenv("EXA_API_KEY", ""))
    raw_jd = ""
    job_source_url = ""

    if job_url:
        # Direct URL fetch
        result = exa.get_contents([job_url], text=True)
        if result.results:
            raw_jd = result.results[0].text or ""
        job_source_url = job_url

    elif search_query:
        # Strip UI filter words that aren't part of the role title
        _STRIP_FROM_QUERY = [
            "hybrid", "remote", "on-site", "onsite", "full-time", "part-time",
            "contract", "internship", "permanent", "full time", "part time",
        ]
        _clean_q = search_query
        for _w in _STRIP_FROM_QUERY:
            _clean_q = _re.sub(rf"\b{_re.escape(_w)}\b",
                               " ", _clean_q, flags=_re.IGNORECASE)
        _clean_q = _re.sub(r"[\s,]+", " ", _clean_q).strip(" ,")

        # Prefix query to target actual job postings, not search-results pages
        _exa_query = f"job opening hiring {_clean_q}"

        include_domains = _PORTAL_DOMAINS.get(portal, [])
        search_kwargs = {
            "num_results": 10,
            "type": "auto",
        }
        if include_domains:
            search_kwargs["include_domains"] = include_domains

        # URL patterns that mean "search results page, not a specific job"
        _SKIP_URL_PATTERNS = [
            "SRCH_", "/jobs-search/", "/job-search/", "search-results",
            "/search?", "?q=", "sortBy=", "?keywords=", "/jobs/search",
        ]

        results = exa.search(_exa_query, **search_kwargs)
        # Pick the first result that looks like a real job posting page
        best_result = None
        for r in (results.results or []):
            if not any(p in r.url for p in _SKIP_URL_PATTERNS):
                best_result = r
                break
        # Fallback: just take first result if all were search pages
        if not best_result and results.results:
            best_result = results.results[0]

        if best_result:
            job_source_url = best_result.url
            # Build a richer JD text from top matching results (not search-result pages)
            good_results = [
                r for r in results.results
                if not any(p in r.url for p in _SKIP_URL_PATTERNS)
            ][:3] or results.results[:3]
            raw_jd = "\n\n".join(
                f"Title: {r.title}\nURL: {r.url}\n"
                f"Summary: {getattr(r, 'text', '')[:500]}"
                for r in good_results
            )

    if not raw_jd:
        raw_jd = "Could not fetch job description."

    portal_note = f" via {portal}" if portal != "Any" and search_query else ""
    return {
        "raw_jd":          raw_jd,
        "job_source_url":  job_source_url,
        "messages": [HumanMessage(
            content=f"Fetched JD{portal_note} ({len(raw_jd)} chars) — {job_source_url or 'no URL'}"
        )],
    }


# ── Node 2: Parse JD with LlamaIndex ─────────────────────────────────────────

class _ParsedJD(BaseModel):
    """Structured job-description fields extracted by LlamaIndex."""
    title: str = Field(default="", description="job title")
    company: str = Field(default="", description="company name")
    summary: str = Field(default="", description="2-sentence role summary")
    requirements: list[str] = Field(
        default_factory=list, description="must-have requirements")
    nice_to_haves: list[str] = Field(
        default_factory=list, description="nice-to-have requirements")
    domain: str = Field(
        default="", description="industry/domain of the company")
    seniority: str = Field(
        default="", description="one of: IC, Manager, Director, VP")


def _parse_jd_langchain(raw_jd: str) -> dict:
    """Fallback JD parser using the LangChain Groq→Azure LLM + JSON prompt."""
    prompt = f"""Extract the following from this job description as JSON:
{{
  "title": "job title",
  "company": "company name",
  "summary": "2-sentence role summary",
  "requirements": ["must-have requirement 1", "must-have requirement 2", ...],
  "nice_to_haves": ["nice-to-have 1", "nice-to-have 2", ...],
  "domain": "industry/domain of the company",
  "seniority": "IC/Manager/Director/VP"
}}

Job Description:
{raw_jd[:6000]}

Return ONLY the JSON object, no markdown fences.
"""
    response = _invoke_llm([HumanMessage(content=prompt)])
    result_text = response.content.strip()
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        return json.loads(match.group()) if match else {}


def parse_jd_node(state: dict) -> dict:
    """
    Parse raw JD text into structured fields using **LlamaIndex** structured
    prediction (Groq LLM). Falls back to the LangChain Groq→Azure JSON path if
    LlamaIndex/Groq errors or is rate-limited.
    """
    raw_jd = state.get("raw_jd", "")

    parsed: dict = {}
    try:
        from llama_index.llms.groq import Groq as _LIGroq
        from llama_index.core.prompts import PromptTemplate

        li_llm = _LIGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
        )
        tmpl = PromptTemplate(
            "You are an expert technical recruiter. Extract the structured "
            "fields from the job description below.\n\n"
            "Job Description:\n{jd_text}\n"
        )
        parsed_obj = li_llm.structured_predict(
            _ParsedJD, tmpl, jd_text=raw_jd[:6000])
        parsed = parsed_obj.model_dump()
    except Exception as _e:
        # Any LlamaIndex/Groq failure (incl. rate limits) → LangChain fallback.
        parsed = _parse_jd_langchain(raw_jd)

    return {
        "parsed_jd": parsed,
        "messages": [AIMessage(content=f"Parsed JD: {parsed.get('title', 'Unknown')} at {parsed.get('company', 'Unknown')}")],
    }


# ── Node 3: Score Both Profiles ───────────────────────────────────────────────

def score_profiles_node(state: dict) -> dict:
    """
    Score IC, Engineering Manager, and Leadership profiles against the JD using:
    1. Chroma semantic similarity (LlamaIndex retrieval) for keyword matching
    2. Groq LLM for holistic scoring and breakdown
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools.vector_store import search_profiles

    parsed_jd = state.get("parsed_jd", {})
    requirements = parsed_jd.get("requirements", [])
    nice_to_haves = parsed_jd.get("nice_to_haves", [])
    all_requirements = requirements + nice_to_haves

    # Build requirement query string
    req_query = "\n".join(
        all_requirements[:20]) if all_requirements else state.get("raw_jd", "")[:1000]

    # Semantic search: retrieve most relevant profile chunks (LlamaIndex → Chroma)
    ic_context = "\n".join(search_profiles(req_query, "IC", k=3))
    em_context = "\n".join(search_profiles(
        req_query, "Engineering Manager", k=3))
    ld_context = "\n".join(search_profiles(req_query, "Leadership", k=3))

    score_prompt = f"""You are an expert ATS (Applicant Tracking System) scorer.

Score these three profiles against the job description. Return ONLY a JSON object.

JOB: {parsed_jd.get('title', '')} at {parsed_jd.get('company', '')}
SENIORITY: {parsed_jd.get('seniority', '')}

MUST-HAVE REQUIREMENTS:
{chr(10).join(f"- {r}" for r in requirements[:15])}

NICE-TO-HAVES:
{chr(10).join(f"- {r}" for r in nice_to_haves[:10])}

IC PROFILE:
{ic_context[:2000]}

ENGINEERING MANAGER PROFILE:
{em_context[:2000]}

LEADERSHIP PROFILE:
{ld_context[:2000]}

Return this JSON:
{{
  "ic_score": <integer 0-100>,
  "ic_strengths": ["strength 1", "strength 2", "strength 3"],
  "ic_gaps": ["gap 1", "gap 2", "gap 3"],
    "engineering_manager_score": <integer 0-100>,
    "engineering_manager_strengths": ["strength 1", "strength 2", "strength 3"],
    "engineering_manager_gaps": ["gap 1", "gap 2", "gap 3"],
  "leadership_score": <integer 0-100>,
  "leadership_strengths": ["strength 1", "strength 2", "strength 3"],
  "leadership_gaps": ["gap 1", "gap 2", "gap 3"],
    "best_profile": "IC" or "Engineering Manager" or "Leadership",
  "reasoning": "one sentence explaining which profile fits better and why"
}}

Be honest and strict — gaps should reflect genuinely missing keywords or experience.
Return ONLY the JSON object.
"""

    response = _invoke_llm([HumanMessage(content=score_prompt)])
    result_text = response.content.strip()

    try:
        scores = json.loads(result_text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        scores = json.loads(match.group()) if match else {}

    best_profile = scores.get("best_profile") or "IC"
    if best_profile not in ("IC", "Engineering Manager", "Leadership"):
        best_profile = "IC"
    result_key = best_profile.lower().replace(" ", "_")
    return {
        "ic_score": scores.get("ic_score", 0),
        "engineering_manager_score": scores.get("engineering_manager_score", 0),
        "leadership_score": scores.get("leadership_score", 0),
        "best_profile": best_profile,
        "strengths": scores.get(f"{result_key}_strengths", []),
        "gaps": scores.get(f"{result_key}_gaps", []),
        "messages": [AIMessage(content=(
            f"IC: {scores.get('ic_score')}/100 | "
            f"Engineering Manager: {scores.get('engineering_manager_score')}/100 | "
            f"Leadership: {scores.get('leadership_score')}/100 | "
            f"Best: {best_profile} — {scores.get('reasoning', '')}"
        ))],
    }


# ── Node 4: Analyse Gaps & Levers ────────────────────────────────────────────

def analyse_gaps_node(state: dict) -> dict:
    """
    For the best-fit profile, generate specific levers (actionable improvements)
    to close each gap and push the ATS score higher.
    """
    parsed_jd = state.get("parsed_jd", {})
    gaps = state.get("gaps", [])
    best_profile = state.get("best_profile", "IC")
    profile_scores = {
        "IC": state.get("ic_score", 0),
        "Engineering Manager": state.get("engineering_manager_score", 0),
        "Leadership": state.get("leadership_score", 0),
    }
    best_score = profile_scores.get(best_profile, 0)

    prompt = f"""You are a career coach and resume expert.

Role: {parsed_jd.get('title', '')} at {parsed_jd.get('company', '')}
Best profile: {best_profile} (score: {best_score}/100)

Gaps identified:
{chr(10).join(f"- {g}" for g in gaps)}

For each gap, suggest a specific, truthful lever to add to the {best_profile} profile.
Levers must quote or reframe evidence already present in the scored profile context.
Never invent projects, systems, vendors, metrics, revenue, savings, locations, or scope.
If a gap has no supporting evidence, return "Do not add without verified experience"
as the lever and identify what evidence the candidate would need to confirm.

Return JSON:
{{
  "levers": [
    {{"gap": "gap description", "lever": "specific action to address it", "grounded_in": "GSK/TESCO/NINA/GIGI experience"}},
    ...
  ],
  "ceiling_score": <estimated score after applying levers>,
  "priority_action": "single most impactful change to make right now"
}}

Return ONLY the JSON object.
"""

    response = _invoke_llm([HumanMessage(content=prompt)])
    try:
        analysis = json.loads(response.content.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        analysis = json.loads(match.group()) if match else {}

    levers = [item.get("lever", "") for item in analysis.get("levers", [])]

    return {
        "levers": levers,
        "messages": [AIMessage(content=(
            f"Gap analysis complete. Ceiling: {analysis.get('ceiling_score', '?')}/100. "
            f"Priority: {analysis.get('priority_action', '')}"
        ))],
    }


# ── Node 6: Update ATS Scores ─────────────────────────────────────────────────

def update_ats_node(state: dict) -> dict:
    """
    Formats a one-line ATS score entry, appends to ats_log.json,
    and rebuilds the cumulative ATS-Report.pdf.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from report import save_and_rebuild

    parsed_jd = state.get("parsed_jd", {})
    ic_score = state.get("ic_score", 0)
    engineering_manager_score = state.get("engineering_manager_score", 0)
    leadership_score = state.get("leadership_score", 0)
    best_profile = state.get("best_profile", "IC")
    profile_scores = {
        "IC": ic_score,
        "Engineering Manager": engineering_manager_score,
        "Leadership": leadership_score,
    }
    best_score = profile_scores.get(best_profile, 0)
    gaps = state.get("gaps", [])
    levers = state.get("levers", [])

    title = parsed_jd.get("title", "Unknown Role")
    company = parsed_jd.get("company", "Unknown Company")

    ic_display = f"**{ic_score}**" if best_profile == "IC" else str(ic_score)
    em_display = (f"**{engineering_manager_score}**"
                  if best_profile == "Engineering Manager"
                  else str(engineering_manager_score))
    ld_display = f"**{leadership_score}**" if best_profile == "Leadership" else str(
        leadership_score)

    ats_entry = (
        f"| — | {company} — {title} | {ic_display} | {em_display} | "
        f"{ld_display} | {best_profile} | {best_score} |"
    )

    # Skip persisting failed runs (empty JD / errored parse → all-zero scores)
    scores_total = (ic_score or 0) + \
        (engineering_manager_score or 0) + (leadership_score or 0)
    run_failed = scores_total == 0 or not (
        parsed_jd.get("title") or parsed_jd.get("company"))
    if run_failed:
        return {
            "ats_entry": ats_entry,
            "messages": [AIMessage(content="Run failed (no JD parsed / zero scores) — not logged to report.")],
        }

    # Persist to JSON log + rebuild PDF
    try:
        pdf_path = save_and_rebuild(state)
        pdf_note = f" · Report saved → {pdf_path.name}"
    except Exception as e:
        pdf_note = f" · PDF error: {e}"

    return {
        "ats_entry": ats_entry,
        "messages": [AIMessage(content=f"ATS entry ready: {ats_entry}{pdf_note}")],
    }
