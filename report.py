"""
report.py — Persistent ATS run log + cumulative PDF report generator.

Every agent run appends a record to `ats_log.json` then rebuilds the full
`ATS-Report.pdf` from scratch so the PDF always contains every run in one file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
ATS_LOG_PATH = _BASE / "output" / "ats_log.json"
ATS_PDF_PATH = _BASE / "output" / "ATS-Report.pdf"
ATS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── JSON log ──────────────────────────────────────────────────────────────────

def append_run(record: dict) -> list[dict]:
    """Append one run record to ats_log.json and return the full list."""
    runs: list[dict] = []
    if ATS_LOG_PATH.exists():
        try:
            runs = json.loads(ATS_LOG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            runs = []
    runs.append(record)
    ATS_LOG_PATH.write_text(
        json.dumps(runs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return runs


def load_runs() -> list[dict]:
    """Return all stored run records."""
    if not ATS_LOG_PATH.exists():
        return []
    try:
        return json.loads(ATS_LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_runs(runs: list[dict]) -> None:
    """Overwrite ats_log.json with the given runs list (for edits / deletes)."""
    ATS_LOG_PATH.write_text(
        json.dumps(runs, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── PDF builder ───────────────────────────────────────────────────────────────

def build_report_pdf(runs: list[dict] | None = None) -> Path:
    """
    Build (or rebuild) ATS-Report.pdf from all stored runs.
    Returns the Path to the generated PDF.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )

    if runs is None:
        runs = load_runs()

    doc = SimpleDocTemplate(
        str(ATS_PDF_PATH),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "RunHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=14,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        leftIndent=12,
        spaceAfter=2,
    )

    story = []

    # ── Cover / summary table ─────────────────────────────────────────────────
    story.append(Paragraph("ATS Score Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}  ·  Runs: {len(runs)}",
        sub_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3 * cm))

    # Summary table header
    table_data = [["#", "Company / Role", "IC", "EM", "LS", "Best", "Date"]]
    for i, r in enumerate(runs, 1):
        ic = r.get("ic_score", 0)
        em = r.get("engineering_manager_score", 0)
        ls = r.get("leadership_score", 0)
        best = r.get("best_profile", "IC")
        ic_txt = f"★{ic}" if best == "IC" else str(ic)
        em_txt = f"★{em}" if best == "Engineering Manager" else str(em)
        ls_txt = f"★{ls}" if best == "Leadership" else str(ls)
        table_data.append([
            str(i),
            f"{r.get('company', '?')} — {r.get('title', '?')}",
            ic_txt,
            em_txt,
            ls_txt,
            best,
            r.get("run_date", "")[:10],
        ])

    col_widths = [0.8 * cm, 7.5 * cm, 1.2 * cm, 1.2 * cm,
                  1.2 * cm, 3.2 * cm, 2.2 * cm]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("ALIGN",       (2, 0), (4, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)

    # ── Per-run detail pages ──────────────────────────────────────────────────
    for i, r in enumerate(runs, 1):
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                     color=colors.HexColor("#eeeeee")))

        ic = r.get("ic_score", 0)
        em = r.get("engineering_manager_score", 0)
        ls = r.get("leadership_score", 0)
        best = r.get("best_profile", "IC")
        title = r.get("title", "Unknown Role")
        company = r.get("company", "Unknown Company")
        url = r.get("url", "")
        run_date = r.get("run_date", "")

        block = []
        block.append(Paragraph(
            f"{i}. {company} &mdash; {title}",
            heading_style,
        ))

        meta_parts = [f"IC: <b>{ic}/100</b>", f"EM: <b>{em}/100</b>",
                      f"LS: <b>{ls}/100</b>",
                      f"Recommended: <b>{best}</b>"]
        if run_date:
            meta_parts.append(run_date[:16])
        block.append(
            Paragraph("  &nbsp;·&nbsp;  ".join(meta_parts), sub_style))

        if url:
            block.append(Paragraph(
                f'<font color="#0066cc"><a href="{url}">{url}</a></font>',
                ParagraphStyle("Link", parent=body_style,
                               textColor=colors.HexColor("#0066cc")),
            ))

        # Score bar (visual)
        best_score = {"IC": ic, "Engineering Manager": em,
                      "Leadership": ls}.get(best, 0)
        bar_pct = int(best_score)
        bar_color = (
            colors.HexColor("#27ae60") if best_score >= 85
            else colors.HexColor("#f39c12") if best_score >= 70
            else colors.HexColor("#e74c3c")
        )
        bar_data = [["", ""]]
        bar_tbl = Table(bar_data, colWidths=[bar_pct * 0.17 * cm, (100 - bar_pct) * 0.17 * cm],
                        rowHeights=[0.35 * cm])
        bar_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), bar_color),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#eeeeee")),
            ("LINEABOVE",  (0, 0), (-1, 0), 0, colors.white),
        ]))
        block.append(Spacer(1, 0.1 * cm))
        block.append(bar_tbl)
        block.append(Spacer(1, 0.15 * cm))

        # Gaps
        gaps = r.get("gaps", [])
        if gaps:
            block.append(Paragraph("<b>Gaps</b>", body_style))
            for g in gaps:
                block.append(Paragraph(f"• {g}", bullet_style))

        # Levers
        levers = r.get("levers", [])
        if levers:
            block.append(Paragraph("<b>Levers</b>", body_style))
            for lv in levers:
                block.append(Paragraph(f"→ {lv}", bullet_style))

        story.append(KeepTogether(block))

    doc.build(story)
    return ATS_PDF_PATH


# ── Public helper called by update_ats_node & app.py ─────────────────────────

def save_and_rebuild(state: dict) -> Path:
    """
    Build a run record from agent state, persist it, regenerate the PDF.
    Returns the Path to the updated PDF.
    """
    parsed = state.get("parsed_jd") or {}
    record = {
        "run_date":         datetime.now().isoformat(timespec="minutes"),
        "title":            parsed.get("title", "Unknown Role"),
        "company":          parsed.get("company", "Unknown Company"),
        "url":              state.get("job_source_url") or state.get("job_url", ""),
        "search_query":     state.get("search_query", ""),
        "domain":           parsed.get("domain", ""),
        "seniority":        parsed.get("seniority", ""),
        "ic_score":         state.get("ic_score", 0),
        "engineering_manager_score": state.get("engineering_manager_score", 0),
        "leadership_score": state.get("leadership_score", 0),
        "best_profile":     state.get("best_profile", "IC"),
        "strengths":        state.get("strengths", []),
        "gaps":             state.get("gaps", []),
        "levers":           state.get("levers", []),
    }
    runs = append_run(record)
    return build_report_pdf(runs)
