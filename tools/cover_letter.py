"""
cover_letter.py — Generate a point-by-point "Your Requirements / My Qualifications"
cover letter by comparing a parsed JD against the recommended profile.

Produces:
  • generate_cover_letter(parsed_jd, best_profile, raw_jd)  -> structured dict
  • render_cover_letter_markdown(data, parsed_jd)           -> markdown preview
  • build_cover_letter_pdf(data, parsed_jd, best_profile)   -> PDF bytes
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent          # job-agent/
_ROOT = _BASE.parent                                     # workspace root

# ── Candidate contact block (env-overridable; keep PII out of source) ─────────
CANDIDATE = {
    "name":     os.getenv("CANDIDATE_NAME", "Your Name"),
    "location": os.getenv("CANDIDATE_LOCATION", "City, ZIP"),
    "phone":    os.getenv("CANDIDATE_PHONE", "+00 00000 00000"),
    "email":    os.getenv("CANDIDATE_EMAIL", "you@example.com"),
    "linkedin": os.getenv("CANDIDATE_LINKEDIN",
                          "https://www.linkedin.com/in/your-handle"),
}

# Profile text sources per recommended profile (env-overridable, matches app.py)
_PROFILE_PATHS = {
    "IC": os.getenv("IC_PROFILE_PATH", "../Profile Summary - IC.txt"),
    "Engineering Manager": os.getenv(
        "ENGINEERING_MANAGER_PROFILE_PATH", "../Balachandar Ramalingam EM.pdf"),
    "Leadership": os.getenv(
        "LEADERSHIP_PROFILE_PATH", "../Balachandar Ramalingam LS - Enhanced.pdf"),
}


def _load_profile_text(best_profile: str) -> str:
    """Return the full text of the recommended profile (.txt or .pdf)."""
    rel = _PROFILE_PATHS.get(best_profile, _PROFILE_PATHS["Leadership"])
    path = (_BASE / rel).resolve()
    if not path.exists():
        return ""
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
        except Exception:
            return ""
    return path.read_text(encoding="utf-8")


def generate_cover_letter(parsed_jd: dict, best_profile: str,
                          raw_jd: str = "") -> dict:
    """
    Build a structured, point-by-point cover letter by matching each JD
    requirement to concrete evidence from the recommended profile.

    Returns a dict:
      {
        "greeting": "Dear Hiring Manager,",
        "intro": "...",
        "pairs": [{"requirement": "...", "qualification": "..."}, ...],
        "closing": "...",
      }
    """
    from agents.nodes import _invoke_llm
    from langchain_core.messages import HumanMessage

    parsed_jd = parsed_jd or {}
    title = parsed_jd.get("title", "") or "the advertised role"
    company = parsed_jd.get("company", "") or "your organisation"
    reqs = parsed_jd.get("requirements") or []
    nice = parsed_jd.get("nice_to_haves") or []
    profile_text = _load_profile_text(best_profile)[:6000]

    req_block = "\n".join(f"- {r}" for r in (reqs + nice)) or "(none parsed)"

    prompt = f"""You are writing a concise, professional cover letter for
{CANDIDATE['name']} applying for "{title}" at "{company}".

Use ONLY evidence that is supported by the candidate PROFILE below. Do NOT invent
employers, metrics, or technologies that are not in the profile. Keep every
qualification to 1–2 sentences, factual and specific.

Produce a point-by-point comparison: for each key job REQUIREMENT, write the
matching candidate qualification drawn from the profile. Pick the 5–7 most
important, distinct requirements (merge duplicates). Phrase each requirement as a
short bold-able heading (3–8 words), not a full sentence.

JOB REQUIREMENTS:
{req_block}

CANDIDATE PROFILE ({best_profile}):
{profile_text}

Return ONLY a JSON object, no markdown fences:
{{
  "greeting": "Dear Hiring Manager,",
  "intro": "2-3 sentence opening that names the role and says a point-by-point comparison of requirements to qualifications follows",
  "pairs": [
    {{"requirement": "short heading", "qualification": "1-2 sentence evidence from profile"}}
  ],
  "closing": "1-2 sentence close noting the CV is attached and offering contact"
}}
"""
    resp = _invoke_llm([HumanMessage(content=prompt)])
    text = (resp.content or "").strip()
    data = _safe_json(text)

    # Defensive defaults so the UI never breaks on a malformed LLM response.
    data.setdefault("greeting", "Dear Hiring Manager,")
    data.setdefault(
        "intro",
        f"I was pleased to see your advertisement for {title} at {company}, as it "
        f"appears to be a very close match with my skills and experience. For your "
        f"convenience, I have included a point-by-point comparison of your stated "
        f"requirements with my qualifications.")
    data.setdefault("closing",
                    "My CV is attached to further expand upon my experience, and I "
                    "would welcome the opportunity to discuss the role with you.")
    if not isinstance(data.get("pairs"), list) or not data["pairs"]:
        data["pairs"] = [{"requirement": r[:60], "qualification": ""}
                         for r in reqs[:6]]
    # Normalise pair keys.
    norm = []
    for p in data["pairs"]:
        if not isinstance(p, dict):
            continue
        req = str(p.get("requirement", "")).strip()
        qual = str(p.get("qualification", "")).strip()
        if req or qual:
            norm.append({"requirement": req, "qualification": qual})
    data["pairs"] = norm
    data["_meta"] = {"title": title, "company": company,
                     "best_profile": best_profile}
    return data


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                return {}
    return {}


def render_cover_letter_markdown(data: dict, parsed_jd: dict) -> str:
    """Render the structured cover letter as markdown for on-screen preview."""
    meta = data.get("_meta", {})
    company = meta.get("company") or (parsed_jd or {}).get("company", "")
    title = meta.get("title") or (parsed_jd or {}).get("title", "")
    today = datetime.now().strftime("%d %B %Y")

    lines = [
        f"**{CANDIDATE['name']}**  ",
        f"{CANDIDATE['location']} · {CANDIDATE['phone']} · {CANDIDATE['email']}  ",
        f"[{CANDIDATE['linkedin']}]({CANDIDATE['linkedin']})",
        "",
        today,
        "",
        f"**{company}**" if company else "",
        "",
        data.get("greeting", "Dear Hiring Manager,"),
        "",
        data.get("intro", ""),
        "",
        "| Your Requirements | My Qualifications |",
        "| --- | --- |",
    ]
    for p in data.get("pairs", []):
        req = p.get("requirement", "").replace("|", "\\|")
        qual = p.get("qualification", "").replace("|", "\\|")
        lines.append(f"| **{req}** | {qual} |")
    lines += ["", data.get("closing", ""), "",
              "Sincerely,", "", CANDIDATE["name"]]
    return "\n".join(l for l in lines if l is not None)


def build_cover_letter_pdf(data: dict, parsed_jd: dict,
                           best_profile: str = "") -> bytes:
    """Render the two-column point-by-point cover letter to PDF bytes."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle)

    meta = data.get("_meta", {})
    company = meta.get("company") or (parsed_jd or {}).get("company", "")
    title = meta.get("title") or (parsed_jd or {}).get("title", "")
    today = datetime.now().strftime("%d %B %Y")

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", parent=styles["Normal"],
                                fontName="Helvetica-Bold", fontSize=15,
                                leading=18, alignment=TA_CENTER, spaceAfter=2)
    contact_style = ParagraphStyle("Contact", parent=styles["Normal"],
                                   fontName="Helvetica", fontSize=9,
                                   leading=12, alignment=TA_CENTER, spaceAfter=1)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=10, leading=14, alignment=TA_JUSTIFY,
                          spaceAfter=6)
    head_col = ParagraphStyle("HeadCol", parent=styles["Normal"],
                              fontName="Helvetica-Bold", fontSize=10,
                              leading=13, textColor=colors.HexColor("#1a1a1a"))
    req_cell = ParagraphStyle("ReqCell", parent=styles["Normal"],
                              fontName="Helvetica-Bold", fontSize=9.5, leading=12)
    qual_cell = ParagraphStyle("QualCell", parent=styles["Normal"],
                               fontName="Helvetica", fontSize=9.5, leading=12)

    link = (f'<a href="{CANDIDATE["linkedin"]}" color="#0a66c2">'
            f'{CANDIDATE["linkedin"].replace("https://www.", "")}</a>')

    story = [
        Paragraph(CANDIDATE["name"].upper(), name_style),
        Paragraph(
            f'{CANDIDATE["location"]} &nbsp;|&nbsp; {CANDIDATE["phone"]} '
            f'&nbsp;|&nbsp; {CANDIDATE["email"]} &nbsp;|&nbsp; {link}',
            contact_style),
        Spacer(1, 14),
        Paragraph(today, body),
    ]
    if company:
        story.append(Paragraph(f"<b>{_esc(company)}</b>", body))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(_esc(data.get("greeting", "Dear Hiring Manager,")), body))
    story.append(Paragraph(_esc(data.get("intro", "")), body))
    story.append(Spacer(1, 4))

    rows = [[Paragraph("Your Requirements", head_col),
             Paragraph("My Qualifications", head_col)]]
    for p in data.get("pairs", []):
        rows.append([
            Paragraph(_esc(p.get("requirement", "")), req_cell),
            Paragraph(_esc(p.get("qualification", "")), qual_cell),
        ])
    table = Table(rows, colWidths=[2.3 * inch, 4.2 * inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#888888")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(_esc(data.get("closing", "")), body))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Sincerely,", body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>{_esc(CANDIDATE['name'])}</b>", body))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                            title=f"Cover Letter — {title}",
                            author=CANDIDATE["name"])
    doc.build(story)
    return buf.getvalue()


def _esc(text: str) -> str:
    """Escape &, <, > for ReportLab, keeping output safe."""
    return (str(text).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))
