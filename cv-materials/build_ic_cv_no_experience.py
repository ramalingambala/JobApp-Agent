#!/usr/bin/env python3
"""Generate an ATS-optimized IC / Forward Deployed Engineer CV WITHOUT the
Professional Experience section (bolded keywords)."""

from cv_parser import parse_cv
import sys as _sys
from pathlib import Path as _P
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable, Table, TableStyle
)
from reportlab.lib import colors

OUTPUT = "Balachandar Ramalingam IC - No Experience.pdf"

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
                                 fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=3, textColor=colors.HexColor("#333333"))
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


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(t, bullet_style), leftIndent=12, value="\u2022")
         for t in items],
        bulletType="bullet", start="\u2022", leftIndent=12, bulletFontSize=9.5,
        spaceBefore=0, spaceAfter=2)


# ── Load content from profile .txt (single source of truth) ─────────────────
_sys.path.insert(0, str(_P(__file__).parent))

_cvdata = parse_cv(_P(__file__).parent / "Profile Summary - IC.txt")

story = []
story.append(Paragraph("BALACHANDAR RAMALINGAM", name_style))
story.append(Paragraph(
    "Bangalore, 560067 &nbsp;|&nbsp; +91 98868 97361 &nbsp;|&nbsp; "
    "ramalingam.bala@gmail.com &nbsp;|&nbsp; linkedin.com/in/BalachandarRamalingam", contact_style))
story.append(Spacer(1, 4))

story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
story.append(hr())
for _i, _para in enumerate(_cvdata["summary_paragraphs"]):
    if _i:
        story.append(Spacer(1, 5))
    story.append(Paragraph(_para, body_style))

story.append(Paragraph("CORE COMPETENCIES", section_style))
story.append(hr())
story.append(Paragraph(_cvdata["competencies"], body_style))

# NOTE: Professional Experience section intentionally omitted in this profile.

story.append(Paragraph("TECHNICAL SKILLS", section_style))
story.append(hr())
_skill_rows = [[Paragraph(k, skill_label_style), Paragraph(v, skill_val_style)]
               for k, v in _cvdata["skills"]]
_skill_table = Table(_skill_rows, colWidths=[1.7 * inch, 5.1 * inch])
_skill_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
]))
story.append(_skill_table)

story.append(Paragraph("CERTIFICATIONS", section_style))
story.append(hr())
story.append(bullets(_cvdata["certifications"]))

story.append(Paragraph("EDUCATION", section_style))
story.append(hr())
story.append(Paragraph(_cvdata["education"], body_style))

doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
                        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                        title="Balachandar Ramalingam - IC CV (No Experience)", author="Balachandar Ramalingam")
doc.build(story)
print("Generated:", OUTPUT)
