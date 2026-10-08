#!/usr/bin/env python3
"""
Build Balachandar Ramalingam LS Okta.pdf from Profile Summary-Leadership-Okta.txt
and compute keyword ATS score against the Okta SRE role requirements.
"""

from cv_parser import parse_cv
import re
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable, Table, TableStyle
)
from reportlab.lib import colors

BASE   = Path(__file__).parent
OUTPUT = str(BASE / "Balachandar Ramalingam LS Okta.pdf")

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

name_style = ParagraphStyle("Name", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=17, leading=20, alignment=TA_CENTER, spaceAfter=2)
contact_style = ParagraphStyle("Contact", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=9.5, leading=13, alignment=TA_CENTER, spaceAfter=1)
section_style = ParagraphStyle("Section", parent=styles["Normal"], fontName="Helvetica-Bold",
                               fontSize=11, leading=14, alignment=TA_LEFT, spaceBefore=10, spaceAfter=4,
                               textColor=colors.HexColor("#1a1a1a"))
role_style = ParagraphStyle("Role", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=10, leading=13, alignment=TA_LEFT, spaceBefore=6, spaceAfter=0)
role_meta_style = ParagraphStyle("RoleMeta", parent=styles["Normal"], fontName="Helvetica-Oblique",
                                 fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=3,
                                 textColor=colors.HexColor("#333333"))
subheader_style = ParagraphStyle("SubHeader", parent=styles["Normal"], fontName="Helvetica-BoldOblique",
                                 fontSize=9.5, leading=13, alignment=TA_LEFT,
                                 spaceBefore=6, spaceAfter=2,
                                 textColor=colors.HexColor("#1a5276"))
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=9.5, leading=13, alignment=TA_JUSTIFY, spaceAfter=2)
bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], fontName="Helvetica",
                              fontSize=9.5, leading=13, alignment=TA_LEFT)
skill_label_style = ParagraphStyle("SkillLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
                                   fontSize=9.5, leading=13)
skill_val_style = ParagraphStyle("SkillVal", parent=styles["Normal"], fontName="Helvetica",
                                 fontSize=9.5, leading=13)


def hr():
    return HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#888888"),
                      spaceBefore=2, spaceAfter=4)


def _make_bullet_list(items):
    return ListFlowable(
        [ListItem(Paragraph(t, bullet_style), leftIndent=12, value="\u2022")
         for t in items],
        bulletType="bullet", start="\u2022", leftIndent=12, bulletFontSize=9.5,
        spaceBefore=0, spaceAfter=2,
    )


def render_bullets(items, story):
    """Flush bullet groups; emit __SUB__: items as styled sub-section headers."""
    pending = []
    for t in items:
        if t.startswith("__SUB__:"):
            if pending:
                story.append(_make_bullet_list(pending))
                pending = []
            story.append(Paragraph(t[8:], subheader_style))
        else:
            pending.append(t)
    if pending:
        story.append(_make_bullet_list(pending))


# ── Load CV data ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE))
_cvdata = parse_cv(BASE / "Profile Summary-Leadership-Okta.txt")

story = []
story.append(Paragraph("BALACHANDAR RAMALINGAM", name_style))
story.append(Paragraph(
    "Bangalore, 560067 &nbsp;|&nbsp; +91 98868 97361 &nbsp;|&nbsp; "
    "ramalingam.bala@gmail.com &nbsp;|&nbsp; linkedin.com/in/BalachandarRamalingam",
    contact_style))
story.append(Spacer(1, 4))

story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
story.append(hr())
for _i, _para in enumerate(_cvdata["summary_paragraphs"]):
    if _i:
        story.append(Spacer(1, 5))
    story.append(Paragraph(_para, body_style))

story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
story.append(hr())
for _exp in _cvdata["experience"]:
    story.append(Paragraph(_exp["header"], role_style))
    story.append(Paragraph(_exp["meta"], role_meta_style))
    render_bullets(_exp["bullets"], story)

story.append(Paragraph("CORE COMPETENCIES", section_style))
story.append(hr())
_skill_rows = [[Paragraph(k, skill_label_style), Paragraph(v, skill_val_style)]
               for k, v in _cvdata["skills"]]
_skill_table = Table(_skill_rows, colWidths=[1.7 * inch, 5.1 * inch])
_skill_table.setStyle(TableStyle([
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ("TOPPADDING",    (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
]))
story.append(_skill_table)

story.append(Paragraph("CERTIFICATIONS", section_style))
story.append(hr())
story.append(_make_bullet_list(_cvdata["certifications"]))

story.append(Paragraph("EDUCATION", section_style))
story.append(hr())
story.append(Paragraph(_cvdata["education"], body_style))

doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
                        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                        title="Balachandar Ramalingam - LS Okta CV",
                        author="Balachandar Ramalingam")
doc.build(story)
print(f"Generated: {OUTPUT}")


# ── ATS keyword scoring ───────────────────────────────────────────────────────
def _plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return text.lower()


def ats_score(profile_path: Path) -> dict:
    profile_text = _plain(profile_path.read_text(encoding="utf-8"))

    # Weighted keyword categories drawn from the Okta SRE JD signals (from agent analysis)
    categories = {
        "SRE / Reliability Engineering": {
            "weight": 25,
            "terms": [
                "site reliability", "sre", "slo", "error budget", "uptime",
                "99.99", "incident response", "post-mortem", "mean-time-to-recovery",
                "mttr", "capacity planning", "runbook", "chaos engineering",
                "reliability", "service-level",
            ],
        },
        "Observability & Monitoring": {
            "weight": 20,
            "terms": [
                "observability", "monitoring", "alerting", "dashboards",
                "azure monitor", "app insights", "langfuse", "tracing",
                "health check", "metrics", "logging",
            ],
        },
        "Kubernetes & Infrastructure": {
            "weight": 20,
            "terms": [
                "kubernetes", "terraform", "infrastructure-as-code", "ci/cd",
                "canary", "rollback", "gitops", "gitlab", "helm", "aks",
                "cloud-native", "microservices",
            ],
        },
        "Cloud Platforms": {
            "weight": 15,
            "terms": [
                "azure", "aws", "gcp", "cloud platform", "multi-tenant",
                "saas", "platform engineering", "cloud operations",
            ],
        },
        "Incident & Ops Leadership": {
            "weight": 10,
            "terms": [
                "incident management", "change management", "problem management",
                "servicenow", "on-call", "escalation", "sla attainment",
            ],
        },
        "Team & Stakeholder Leadership": {
            "weight": 10,
            "terms": [
                "team leadership", "senior leadership", "50+", "engineering manager",
                "mentoring", "coaching", "product manager", "cross-functional",
            ],
        },
    }

    total_weighted = 0.0
    total_weight   = sum(c["weight"] for c in categories.values())
    results = {}

    for cat, cfg in categories.items():
        hits   = [t for t in cfg["terms"] if t in profile_text]
        ratio  = len(hits) / len(cfg["terms"])
        contrib = ratio * cfg["weight"]
        total_weighted += contrib
        results[cat] = {
            "matched": hits,
            "missed":  [t for t in cfg["terms"] if t not in profile_text],
            "score":   round(ratio * 100),
            "weight":  cfg["weight"],
        }

    overall = round(total_weighted / total_weight * 100)
    return {"overall": overall, "categories": results}


score_data = ats_score(BASE / "Profile Summary-Leadership-Okta.txt")

print("\n" + "=" * 60)
print(f"  ATS Score — Okta SRE (Leadership profile): {score_data['overall']}/100")
print("=" * 60)
for cat, d in score_data["categories"].items():
    bar = "█" * (d["score"] // 10) + "░" * (10 - d["score"] // 10)
    print(f"\n  {cat} (weight {d['weight']}%) — {d['score']}%")
    print(f"  [{bar}]")
    if d["missed"]:
        print(f"  Gaps: {', '.join(d['missed'][:5])}")
print()
