"""
Generate a technical-assessment PDF documenting the Job Application Agent codebase.

Run:  venv/bin/python docs/generate_assessment_pdf.py
Output: docs/Codebase-Technical-Assessment.pdf
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0F2A43")
BLUE = colors.HexColor("#1F6FEB")
TEAL = colors.HexColor("#0B7285")
LIGHT = colors.HexColor("#EAF1FB")
GREY = colors.HexColor("#5A6672")
ROWALT = colors.HexColor("#F5F8FC")
GREEN = colors.HexColor("#1B7F4B")
RED = colors.HexColor("#B23A3A")

OUT_PATH = Path(__file__).parent / "Codebase-Technical-Assessment.pdf"

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleBig", parent=ss["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=30, textColor=NAVY, spaceAfter=6,
)
subtitle_style = ParagraphStyle(
    "Subtitle", parent=ss["Normal"], fontName="Helvetica",
    fontSize=12.5, leading=17, textColor=GREY, alignment=TA_CENTER, spaceAfter=2,
)
h1 = ParagraphStyle(
    "H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, leading=20, textColor=colors.white,
    backColor=NAVY, borderPadding=(6, 8, 6, 8), spaceBefore=16, spaceAfter=10,
)
h2 = ParagraphStyle(
    "H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
    fontSize=12.5, leading=16, textColor=BLUE, spaceBefore=10, spaceAfter=5,
)
body = ParagraphStyle(
    "Body", parent=ss["Normal"], fontName="Helvetica",
    fontSize=10, leading=15, textColor=colors.HexColor("#1B2430"),
    alignment=TA_JUSTIFY, spaceAfter=6,
)
body_left = ParagraphStyle(
    "BodyLeft", parent=body, alignment=TA_LEFT,
)
bullet = ParagraphStyle(
    "Bullet", parent=body, alignment=TA_LEFT, spaceAfter=2, leading=14,
)
cell = ParagraphStyle(
    "Cell", parent=ss["Normal"], fontName="Helvetica",
    fontSize=8.8, leading=12, textColor=colors.HexColor("#1B2430"),
)
cell_b = ParagraphStyle(
    "CellB", parent=cell, fontName="Helvetica-Bold", textColor=NAVY,
)
cell_head = ParagraphStyle(
    "CellHead", parent=cell, fontName="Helvetica-Bold", textColor=colors.white,
)
code_style = ParagraphStyle(
    "Code", parent=ss["Normal"], fontName="Courier", fontSize=9, leading=13,
    textColor=NAVY, backColor=LIGHT, borderPadding=(6, 6, 6, 6), spaceAfter=8,
)
small = ParagraphStyle(
    "Small", parent=body, fontSize=8.5, leading=11, textColor=GREY,
)

story = []


def P(text, style=body):
    story.append(Paragraph(text, style))


def gap(h=6):
    story.append(Spacer(1, h))


def section(text):
    story.append(Paragraph(text, h1))


def sub(text):
    story.append(Paragraph(text, h2))


def bullets(items):
    flow = [ListItem(Paragraph(t, bullet), leftIndent=6, value="•")
            for t in items]
    story.append(ListFlowable(flow, bulletType="bullet",
                 bulletColor=BLUE, leftIndent=12, spaceAfter=6))


def make_table(data, col_widths, header=True, alt=True, small_font=False):
    st = cell if not small_font else ParagraphStyle(
        "Cell2", parent=cell, fontSize=8.2, leading=11)
    rows = []
    for r_i, row in enumerate(data):
        new_row = []
        for c_i, val in enumerate(row):
            if r_i == 0 and header:
                new_row.append(Paragraph(str(val), cell_head))
            elif c_i == 0:
                new_row.append(Paragraph(str(val), cell_b))
            else:
                new_row.append(Paragraph(str(val), st))
        rows.append(new_row)
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D6E5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    if alt:
        for r_i in range(1, len(data)):
            if r_i % 2 == 0:
                style.append(("BACKGROUND", (0, r_i), (-1, r_i), ROWALT))
    t.setStyle(TableStyle(style))
    story.append(t)
    gap(8)


# ══════════════════════════════════════════════════════════════════════════════
# COVER
# ══════════════════════════════════════════════════════════════════════════════
gap(40)
story.append(HRFlowable(width="100%", thickness=3, color=BLUE, spaceAfter=14))
P("Job Application Agent", title_style)
P("Codebase Technical Assessment", subtitle_style)
P("An agentic AI system that scores professional profiles against job "
  "descriptions using LangGraph, LlamaIndex RAG, and multi-provider LLMs", subtitle_style)
story.append(HRFlowable(width="100%", thickness=3, color=BLUE,
             spaceBefore=14, spaceAfter=20))
gap(10)

overview_tbl = [
    ["Aspect", "Summary"],
    ["Domain", "Career / recruitment automation (personal ATS-style scorer)"],
    ["Core pattern",
        "Agentic pipeline (LangGraph) + Retrieval-Augmented Generation"],
    ["Primary language", "Python 3.13"],
    ["Interfaces", "Streamlit web app + CLI (main.py)"],
    ["LLMs",
        "Groq Llama-3.3-70B (primary) · Azure OpenAI GPT-4o-mini (fallback)"],
    ["Retrieval", "LlamaIndex + Chroma + local HuggingFace embeddings"],
    ["Job data", "Exa neural search / contents API (SDK + optional MCP)"],
]
make_table(overview_tbl, [4.2 * cm, 11.3 * cm])
P("Prepared for technical assessment. All statements below are grounded in the "
  "actual repository modules: <font face='Courier'>app.py</font>, "
  "<font face='Courier'>agents/graph.py</font>, <font face='Courier'>agents/nodes.py</font>, "
  "<font face='Courier'>tools/vector_store.py</font>, <font face='Courier'>tools/exa_mcp.py</font>, "
  "<font face='Courier'>report.py</font> and <font face='Courier'>state.py</font>.", small)

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# 1. BUSINESS USE CASE
# ══════════════════════════════════════════════════════════════════════════════
section("1 &nbsp; Business Use Case")

sub("The problem")
P("Tailoring a CV or professional profile to each individual job posting is slow, "
  "repetitive and subjective. Applicant Tracking Systems (ATS) reward keyword and "
  "experience alignment, but a candidate cannot easily tell — for any given job — "
  "whether they should apply as an <b>individual contributor (IC)</b> or in a "
  "<b>leadership</b> capacity, which specific requirements they miss, and what to "
  "change to raise their match score.")

sub("The solution")
P("The <b>Job Application Agent</b> is an AI assistant that ingests a job "
  "description, extracts its structured requirements, and scores the candidate's "
  "two maintained profiles (IC and Leadership) against it. For each job it returns "
  "an ATS-style score out of 100 per profile, recommends the stronger profile, "
  "lists strengths and gaps, and proposes grounded, actionable \u201clevers\u201d to "
  "close those gaps. Every run is appended to a persistent log and a cumulative "
  "PDF ATS report is rebuilt automatically.")

sub("Who uses it and how")
bullets([
    "<b>User:</b> a single job seeker evaluating many postings quickly and objectively.",
    "<b>Inputs (3 reliable modes):</b> a single <b>Job URL</b>, a <b>file/paste of many "
    "Job URLs</b> (bulk scoring), or <b>pasted JD text</b>.",
    "<b>Outputs:</b> IC score /100, Leadership score /100, recommended profile, "
    "strengths, gaps, improvement levers, and a downloadable cumulative ATS report PDF.",
    "<b>Value:</b> converts a subjective, manual triage into a repeatable, evidence-grounded "
    "scoring workflow — decide fast where to invest application effort.",
])

sub("Business outcomes")
bullets([
    "Faster shortlisting of which roles are worth applying to.",
    "Objective, side-by-side IC-vs-Leadership positioning per role.",
    "A running record (JSON + PDF) that documents fit across all evaluated jobs.",
    "Zero external data/embedding cost — the corpus and vectors stay fully local.",
])

# ══════════════════════════════════════════════════════════════════════════════
# 2. ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
section("2 &nbsp; Solution Architecture")

P("The system is orchestrated as a <b>LangGraph state machine</b> — a typed, linear "
  "pipeline of five nodes. Each node reads and writes a shared, typed state object "
  "(<font face='Courier'>JobAgentState</font>) and emits progress messages that the "
  "Streamlit UI streams live.")

P("<b>Pipeline:</b> START &rarr; fetch_jd &rarr; parse_jd &rarr; score_profiles "
  "&rarr; analyse_gaps &rarr; update_ats &rarr; END", code_style)

stage_tbl = [
    ["Stage", "Node", "What it does", "Key tech"],
    ["1", "fetch_jd",
     "Retrieves the JD text from a URL (or search query) and captures the source URL.",
     "Exa (exa-py)"],
    ["2", "parse_jd",
     "Extracts structured fields (title, company, requirements, nice-to-haves, domain, "
     "seniority) into a Pydantic model.",
     "LlamaIndex structured_predict"],
    ["3", "score_profiles",
     "RAG: retrieves the most relevant IC & Leadership profile chunks and scores both "
     "against the JD requirements.",
     "Chroma + LlamaIndex retriever + Groq LLM"],
    ["4", "analyse_gaps",
     "Turns each identified gap into a concrete, grounded improvement \u201clever\u201d.",
     "Groq LLM"],
    ["5", "update_ats",
     "Appends the run to ats_log.json and rebuilds the cumulative ATS-Report.pdf.",
     "ReportLab"],
]
make_table(stage_tbl, [1.0 * cm, 2.5 * cm,
           8.2 * cm, 3.8 * cm], small_font=True)

sub("Shared state")
P("A single <font face='Courier'>TypedDict</font> carries data across nodes: the job "
  "URL / search query, the raw and parsed JD, IC & Leadership scores, best profile, "
  "strengths, gaps, levers, the ATS entry, and a LangGraph-reduced message log. This "
  "makes the flow inspectable and each node independently testable.")

sub("Two front-ends")
bullets([
    "<b>Streamlit</b> (<font face='Courier'>app.py</font>): a two-tab UI — an <b>Agent</b> "
    "tab for scoring and a <b>Reports</b> tab for the cumulative ATS report.",
    "<b>CLI</b> (<font face='Courier'>main.py</font>): headless single-run scoring plus a "
    "<font face='Courier'>--refresh-profiles</font> re-index command.",
])

# ══════════════════════════════════════════════════════════════════════════════
# 3. TECH STACK
# ══════════════════════════════════════════════════════════════════════════════
section("3 &nbsp; Tech Stack, Frameworks &amp; Tools")

P("The solution deliberately combines two AI frameworks — <b>LangChain/LangGraph</b> "
  "for orchestration and LLM provider abstraction, and <b>LlamaIndex</b> for structured "
  "extraction and RAG ingestion/retrieval — each used where it is strongest.")

stack_tbl = [
    ["Layer", "Technology", "Role in the solution"],
    ["Orchestration", "LangGraph",
     "Defines the 5-node StateGraph pipeline; streams node updates to the UI."],
    ["LLM framework", "LangChain (core, groq, openai)",
     "Provider abstraction; wraps Groq (primary) and Azure OpenAI (fallback); prompt/message plumbing."],
    ["Structured AI + RAG", "LlamaIndex",
     "structured_predict for JD parsing; VectorStoreIndex + SentenceSplitter + metadata filters for retrieval."],
    ["LLM (primary)", "Groq — llama-3.3-70b-versatile",
     "Fast, low-cost inference for parsing, scoring and gap analysis (temperature 0)."],
    ["LLM (fallback)", "Azure OpenAI / OpenAI — gpt-4o-mini",
     "Automatic failover when Groq is rate-limited."],
    ["Embeddings", "HuggingFace all-MiniLM-L6-v2",
     "Local CPU sentence embeddings (~80MB, cached) — no API key, no cost."],
    ["Vector store", "Chroma (persistent, local)",
     "Stores profile chunk vectors in ./chroma_db (collection 'profiles_li')."],
    ["Job data", "Exa (exa-py) + optional Exa MCP",
     "Neural search & full-content fetch of job postings; MCP variant via langchain-mcp-adapters."],
    ["Web UI", "Streamlit",
     "Interactive app: input modes, live progress, metrics, tables, downloads."],
    ["Reporting", "ReportLab",
     "Generates the cumulative ATS-Report.pdf from the JSON run log."],
    ["Observability", "LangSmith (optional)",
     "Tracing of LLM/graph runs when LANGCHAIN_TRACING_V2 is enabled."],
    ["Data models", "Pydantic v2",
     "Typed _ParsedJD schema enforced during structured extraction."],
    ["Config / secrets", "python-dotenv (.env)",
     "Loads API keys and paths; keeps secrets out of source."],
    ["Proxy handling", "ssl_patch.py",
     "Points REQUESTS_CA_BUNDLE / SSL_CERT_FILE at a corporate proxy CA bundle."],
]
make_table(stack_tbl, [2.7 * cm, 4.3 * cm, 8.5 * cm], small_font=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. HOW AI IS PLUGGED IN
# ══════════════════════════════════════════════════════════════════════════════
section("4 &nbsp; How AI Is Plugged In")

sub("Where the LLM is called")
P("The LLM is used at three distinct stages of the pipeline, each with a purpose-built "
  "prompt and deterministic settings (<font face='Courier'>temperature = 0</font>) for "
  "reproducible results:")
bullets([
    "<b>JD parsing</b> — LlamaIndex <font face='Courier'>structured_predict</font> maps free "
    "JD text onto the <font face='Courier'>_ParsedJD</font> Pydantic schema.",
    "<b>Profile scoring</b> — a strict ATS prompt returns a JSON object with IC/Leadership "
    "scores, strengths, gaps and the recommended profile.",
    "<b>Gap analysis</b> — a coaching prompt turns gaps into grounded, actionable levers.",
])

sub("Multi-provider resilience")
P("A single helper, <font face='Courier'>_invoke_llm(messages)</font>, calls Groq first "
  "and transparently fails over to Azure OpenAI / OpenAI when a rate-limit signal is "
  "detected (matching on <font face='Courier'>rate_limit, 429, quota, too many requests</font>). "
  "LLM clients are lazily instantiated and cached as singletons.")

P("try:&nbsp;&nbsp;return get_llm().invoke(messages)&nbsp;&nbsp;# Groq<br/>"
  "except Exception as e:&nbsp;&nbsp;# on rate-limit &rarr; Azure/OpenAI fallback<br/>"
  "&nbsp;&nbsp;&nbsp;&nbsp;if any(sig in str(e).lower() for sig in RATE_LIMIT_SIGNALS):<br/>"
  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return get_fallback_llm().invoke(messages)",
  code_style)

sub("Robustness patterns")
bullets([
    "<b>Schema-first extraction:</b> structured_predict reduces malformed-JSON risk; a "
    "LangChain JSON path with regex extraction is the fallback if LlamaIndex/Groq errors.",
    "<b>Deterministic scoring:</b> temperature 0 keeps scores stable across identical inputs.",
    "<b>Graceful degradation:</b> every stage has a fallback so one provider or parser "
    "failure does not break the run.",
])

# ══════════════════════════════════════════════════════════════════════════════
# 5. HOW RAG IS USED
# ══════════════════════════════════════════════════════════════════════════════
section("5 &nbsp; How RAG (Retrieval-Augmented Generation) Is Used")

P("RAG is the core of the scoring stage. Rather than pasting entire multi-page profiles "
  "into the prompt (costly and noisy), the system retrieves only the profile passages "
  "most relevant to each job's requirements and grounds the LLM's score in that evidence.")

sub("Ingestion pipeline (LlamaIndex \u2192 Chroma)")
ingest_tbl = [
    ["Step", "Detail"],
    ["1. Load", "IC and Leadership profile .txt files become LlamaIndex Documents, tagged with "
     "metadata profile_type = 'IC' | 'Leadership'."],
    ["2. Chunk", "SentenceSplitter(chunk_size=512, chunk_overlap=64) splits each profile into "
     "semantically coherent nodes (~12 chunks from 2 profiles)."],
    ["3. Embed",
        "Each chunk is embedded locally with HuggingFace all-MiniLM-L6-v2 (CPU, normalized)."],
    ["4. Persist", "Vectors + metadata are written to a local Chroma collection ('profiles_li') "
     "via ChromaVectorStore, persisted under ./chroma_db."],
]
make_table(ingest_tbl, [2.6 * cm, 12.9 * cm], small_font=True)

sub("Retrieval &amp; augmentation")
bullets([
    "For each JD, the parsed requirements + nice-to-haves are concatenated into a query string.",
    "A <b>metadata-filtered retriever</b> fetches the top-<b>k=3</b> chunks for <b>IC</b> and, "
    "separately, the top-3 for <b>Leadership</b> (MetadataFilters on profile_type).",
    "The retrieved chunks are injected into the scoring prompt, so the LLM scores each persona "
    "against real, targeted evidence — not the whole profile and not hallucinated experience.",
    "<font face='Courier'>refresh_profiles()</font> re-ingests (reset=True) after profile edits; "
    "the index is otherwise cached and reused without re-embedding.",
])

sub("Why RAG fits this problem")
bullets([
    "<b>Two personas, one query:</b> metadata filtering cleanly separates IC vs Leadership "
    "evidence from a shared store.",
    "<b>Context efficiency:</b> only the most relevant passages enter the prompt, improving "
    "keyword-level scoring accuracy and controlling token usage.",
    "<b>Local &amp; private:</b> embeddings and vectors never leave the machine — no embedding "
    "API cost and no data egress.",
])

# ══════════════════════════════════════════════════════════════════════════════
# 6. PROS & CONS
# ══════════════════════════════════════════════════════════════════════════════
section("6 &nbsp; Pros &amp; Cons of the Tools Chosen")

pc_tbl = [
    ["Tool", "Pros", "Cons / trade-offs"],
    ["LangGraph",
     "Explicit typed state; inspectable, testable nodes; easy to add/remove stages; native streaming.",
     "Extra abstraction for a currently linear flow; another dependency to learn."],
    ["LangChain",
     "Uniform LLM interface; trivial provider swap/fallback; rich ecosystem.",
     "Fast-moving API surface; heavier dependency; occasional breaking changes."],
    ["LlamaIndex",
     "First-class structured extraction; ergonomic RAG ingestion & metadata filtering.",
     "Overlaps LangChain in scope; running both adds cognitive load and deps."],
    ["Groq (Llama 3.3)",
     "Very fast and cheap; strong 70B quality for parsing/scoring.",
     "Tight rate limits on free tier (drove the fallback design)."],
    ["Azure OpenAI (fallback)",
     "Reliable, enterprise-grade, higher limits; smooth failover target.",
     "Paid; requires endpoint/key setup; adds a second provider to manage."],
    ["HuggingFace MiniLM",
     "Local, free, private, no API key; good quality for short corpora.",
     "CPU embedding is slower at scale; ~80MB first-time model download."],
    ["Chroma",
     "Zero-config, local, persistent; ideal for a small corpus.",
     "Not built for very large / multi-tenant / distributed workloads."],
    ["Exa",
     "Neural search + clean full-content fetch of postings via one API.",
     "Index coverage of gated boards (LinkedIn/Glassdoor) is sparse & fuzzy."],
    ["MCP (Exa server)",
     "Standardised tool protocol; portable across agents; resume-relevant.",
     "Needs Node.js/npx; less dependable than the SDK — SDK kept as fallback."],
    ["Streamlit",
     "Very fast to build data UIs; live progress; minimal front-end code.",
     "Single-user session model; limited layout control; not for high-concurrency."],
    ["ReportLab",
     "Precise, dependency-light PDF generation entirely in Python.",
     "Verbose imperative layout API compared with HTML-to-PDF tools."],
]
make_table(pc_tbl, [2.6 * cm, 6.6 * cm, 6.3 * cm], small_font=True)

# ══════════════════════════════════════════════════════════════════════════════
# 7. LEARNINGS / EVOLUTION
# ══════════════════════════════════════════════════════════════════════════════
section("7 &nbsp; Learnings &mdash; Evolution From Start to End")

sub("What changed over the build")
change_tbl = [
    ["Area", "Started as", "Ended as", "Why"],
    ["Retrieval stack", "LangChain-only Chroma ('profiles' collection)",
     "LlamaIndex ingestion + retrieval ('profiles_li')",
     "Structured extraction + metadata-filtered RAG; avoid schema clash."],
    ["JD parsing", "LLM + hand-parsed JSON",
     "LlamaIndex structured_predict (+ JSON fallback)",
     "Schema-enforced output; fewer parse failures."],
    ["LLM reliability", "Single provider (Groq)",
     "Groq \u2192 Azure/OpenAI auto-fallback",
     "Free-tier rate limits interrupted runs."],
    ["Job sourcing", "Search Query, LinkedIn URL, Glassdoor crawl (+cookie)",
     "Job URL, Job URLs file, Paste JD text",
     "Scraping/search returned wrong or no jobs; simplified to reliable inputs."],
    ["Cover letter", "LLM cover-letter node + UI",
     "Removed",
     "Out of scope for scoring; reduced surface area and cost."],
]
make_table(change_tbl, [2.4 * cm, 4.5 * cm,
           4.4 * cm, 4.2 * cm], small_font=True)

sub("Key engineering lessons")
bullets([
    "<b>Prefer reliable inputs over brittle scraping.</b> LinkedIn blocks crawlers and "
    "Glassdoor's 'Jobs for you' feed renders client-side; Exa's index of these is fuzzy. "
    "Deterministic URL/paste inputs produce far better results than automated search.",
    "<b>Design for provider limits up front.</b> A thin fallback wrapper (_invoke_llm) turned "
    "rate-limit failures from run-killers into transparent retries.",
    "<b>Use the right framework per job.</b> LangChain for provider abstraction; LlamaIndex for "
    "structured extraction and RAG — combined rather than forcing one to do everything.",
    "<b>Isolate cross-cutting concerns.</b> Secrets in .env; corporate-proxy TLS in ssl_patch.py "
    "imported first; a separate collection name to prevent vector-schema conflicts.",
    "<b>Keep the graph lean.</b> Removing unused modes/nodes reduced cost, failure points and "
    "cognitive load without losing core value.",
    "<b>Ground the model.</b> Metadata-filtered RAG + temperature 0 makes scoring more honest, "
    "repeatable and defensible than free-form prompting.",
])

# ══════════════════════════════════════════════════════════════════════════════
# 8. FAQ
# ══════════════════════════════════════════════════════════════════════════════
section("8 &nbsp; FAQ (Anticipated Assessment Questions)")


def faq(q, a):
    story.append(Paragraph("Q. " + q, ParagraphStyle(
        "FQ", parent=body_left, fontName="Helvetica-Bold", textColor=NAVY,
        spaceAfter=2, spaceBefore=6)))
    story.append(Paragraph("A. " + a, body_left))


faq("Why LangGraph instead of a plain script or a LangChain chain?",
    "The workflow is a series of stateful stages that must be inspectable, individually "
    "testable and streamable to the UI. LangGraph gives a typed shared state and explicit "
    "nodes/edges, so stages can be added, removed or reordered safely — which is exactly "
    "what happened when the cover-letter node was removed.")

faq("Why use both LangChain and LlamaIndex \u2014 isn't that redundant?",
    "They are used for complementary strengths. LangChain provides the LLM provider "
    "abstraction and the Groq\u2192Azure fallback; LlamaIndex provides schema-enforced "
    "structured extraction and an ergonomic, metadata-filtered RAG pipeline. Each does what "
    "it is best at.")

faq("Why local embeddings and Chroma rather than a cloud vector database?",
    "The corpus is tiny (two profiles) and private. Local MiniLM embeddings + local Chroma "
    "mean zero API cost, no data egress, and offline operation. A cloud store would add cost "
    "and complexity with no benefit at this scale.")

faq("How do you stop the LLM from hallucinating scores?",
    "Three controls: (1) RAG grounds scoring in retrieved, real profile passages; (2) "
    "temperature 0 makes output deterministic; (3) a strict prompt demands honest gaps and a "
    "fixed JSON schema. Scoring is still model-assisted judgement, so it is decision-support, "
    "not an absolute measure \u2014 a known limitation.")

faq("How is rate limiting handled?",
    "_invoke_llm calls Groq first and, on any rate-limit signal (rate_limit/429/quota/too many "
    "requests), transparently retries on Azure OpenAI / OpenAI. Bulk scoring also spaces calls "
    "to stay within limits.")

faq("Why were the search / LinkedIn / Glassdoor modes removed?",
    "They did not reliably return the right jobs: LinkedIn blocks automated crawling, "
    "Glassdoor's personalised feed is client-side rendered, and Exa's index of those boards is "
    "sparse and fuzzy. The app was simplified to deterministic inputs (Job URL, URL file, "
    "pasted JD) that consistently work.")

faq("How is the ATS report persisted and kept consistent?",
    "Each run appends a record to output/ats_log.json, then the full ATS-Report.pdf is rebuilt "
    "from the log with ReportLab. Rebuilding from the source of truth guarantees the PDF always "
    "reflects every run.")

faq("How are secrets and corporate-proxy TLS handled?",
    "All keys and paths load from .env via python-dotenv (never hard-coded). ssl_patch.py is "
    "imported first in both entry points to point the TLS trust store at an optional corporate "
    "proxy CA bundle so model downloads and HTTPS calls succeed behind an inspecting proxy.")

faq("What are the main limitations today?",
    "It is single-user; scoring is sequential (with deliberate pauses for rate limits); job "
    "sourcing relies on user-supplied URLs; and scores reflect LLM judgement. These are "
    "acceptable for a personal tool but would need work for production.")

faq("How would you productionise this?",
    "Add async/batch scoring and caching; a provider pool with health-based routing; a proper "
    "evaluation harness (e.g. LangSmith datasets) to measure scoring quality; authentication and "
    "multi-user persistence; and a managed vector store if the corpus grows beyond a handful of "
    "profiles.")

faq("What is the role of MCP here?",
    "Exa is integrated through the Model Context Protocol (via langchain-mcp-adapters) as a "
    "standardised, portable tool interface, with the direct Exa SDK kept as a dependable "
    "fallback when Node.js/MCP is unavailable.")

gap(10)
story.append(HRFlowable(width="100%", thickness=1,
             color=colors.HexColor("#C9D6E5")))
gap(4)
P("Generated from the live codebase for technical-assessment purposes. Pipeline: "
  "fetch_jd &rarr; parse_jd &rarr; score_profiles &rarr; analyse_gaps &rarr; update_ats.", small)


# ── Footer with page numbers ──────────────────────────────────────────────────
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.1 * cm,
                      "Job Application Agent — Codebase Technical Assessment")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#C9D6E5"))
    canvas.line(2 * cm, 1.4 * cm, A4[0] - 2 * cm, 1.4 * cm)
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUT_PATH), pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm,
    topMargin=1.6 * cm, bottomMargin=1.8 * cm,
    title="Job Application Agent — Codebase Technical Assessment",
    author="Job Application Agent",
)
doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
print(f"✅ PDF written: {OUT_PATH}")
