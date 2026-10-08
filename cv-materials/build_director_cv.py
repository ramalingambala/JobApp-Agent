#!/usr/bin/env python3
"""Generate an ATS-optimized Director CV (bolded keywords)."""

from cv_parser import parse_cv
import os
import sys as _sys
from pathlib import Path as _P
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable,
    PageBreak, KeepTogether, Table, TableStyle
)
from reportlab.lib import colors

OUTPUT = os.getenv("CV_OUTPUT", "Balachandar Ramalingam LS.pdf")
PROFILE = os.getenv("CV_PROFILE", "Profile Summary-Leadership.txt")
TITLE_LINE = os.getenv("CV_TITLE_LINE", "")
ATS_SPLIT_EXPERIENCE = os.getenv("CV_ATS_SPLIT_EXPERIENCE") == "1"
ATS_ONELINE_EXPERIENCE = os.getenv("CV_ATS_ONELINE_EXPERIENCE") == "1"
PAGE_BREAK_BEFORE_SECOND_ROLE = (
    os.getenv("CV_PAGE_BREAK_BEFORE_SECOND_ROLE") == "1"
)
PAGE_BREAK_BEFORE_COMPETENCIES = (
    os.getenv("CV_PAGE_BREAK_BEFORE_COMPETENCIES") == "1"
)

styles = getSampleStyleSheet()
name_style = ParagraphStyle("Name", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=17, leading=20, alignment=TA_CENTER, spaceAfter=2)
contact_style = ParagraphStyle("Contact", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=9.5, leading=13, alignment=TA_CENTER, spaceAfter=1)
title_style = ParagraphStyle("Title", parent=styles["Normal"], fontName="Helvetica-Bold",
                             fontSize=10.5, leading=13, alignment=TA_CENTER, spaceAfter=3,
                             textColor=colors.HexColor("#333333"))
section_style = ParagraphStyle("Section", parent=styles["Normal"], fontName="Helvetica-Bold",
                               fontSize=11, leading=14, alignment=TA_LEFT, spaceBefore=10, spaceAfter=4,
                               textColor=colors.HexColor("#1a1a1a"))
role_style = ParagraphStyle("Role", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=10, leading=13, alignment=TA_LEFT, spaceBefore=6, spaceAfter=0)
company_style = ParagraphStyle("Company", parent=styles["Normal"], fontName="Helvetica-Bold",
                               fontSize=9.5, leading=12, alignment=TA_LEFT, spaceAfter=0)
role_meta_style = ParagraphStyle("RoleMeta", parent=styles["Normal"], fontName="Helvetica-Oblique",
                                 fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=3, textColor=colors.HexColor("#333333"))
role_meta_right_style = ParagraphStyle("RoleMetaRight", parent=styles["Normal"], fontName="Helvetica-Oblique",
                                       fontSize=9, leading=13, alignment=TA_RIGHT, textColor=colors.HexColor("#333333"))
role_left_style = ParagraphStyle("RoleLeft", parent=styles["Normal"], fontName="Helvetica-Bold",
                                 fontSize=10, leading=13, alignment=TA_LEFT)
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

_cvdata = parse_cv(_P(__file__).parent / PROFILE)

story = []
story.append(Paragraph("BALACHANDAR RAMALINGAM", name_style))
if TITLE_LINE:
    story.append(Paragraph(TITLE_LINE, title_style))
story.append(Paragraph(
    "Bangalore, 560067 &nbsp;|&nbsp; +91 98868 97361 &nbsp;|&nbsp; "
    "ramalingam.bala@gmail.com &nbsp;|&nbsp; "
    '<a href="https://www.linkedin.com/in/BalachandarRamalingam" color="#0a66c2">'
    "linkedin.com/in/BalachandarRamalingam</a>", contact_style))
story.append(Spacer(1, 4))

story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
story.append(hr())
for _i, _para in enumerate(_cvdata["summary_paragraphs"]):
    if _i:
        story.append(Spacer(1, 5))
    story.append(Paragraph(_para, body_style))

story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
story.append(hr())
for _exp_index, _exp in enumerate(_cvdata["experience"]):
    if PAGE_BREAK_BEFORE_SECOND_ROLE and _exp_index == 1:
        story.append(PageBreak())
    if ATS_ONELINE_EXPERIENCE:
        _right_bits = [b for b in (
            _exp.get("location"), _exp.get("dates")) if b]
        _right = " &nbsp;|&nbsp; ".join(_right_bits)
        _row = Table(
            [[Paragraph(_exp["header"], role_left_style),
              Paragraph(_right, role_meta_right_style)]],
            colWidths=[4.55 * inch, 2.75 * inch])
        _row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(KeepTogether([_row]))
    elif ATS_SPLIT_EXPERIENCE:
        _head = [Paragraph(_exp["title"], role_style),
                 Paragraph(_exp["company"], company_style)]
        if _exp.get("location"):
            _head.append(Paragraph(_exp["location"], role_meta_style))
        if _exp.get("dates"):
            _head.append(Paragraph(_exp["dates"], role_meta_style))
        story.append(KeepTogether(_head))
    else:
        story.append(Paragraph(_exp["header"], role_style))
        story.append(Paragraph(_exp["meta"], role_meta_style))
    story.append(bullets(_exp["bullets"]))

if PAGE_BREAK_BEFORE_COMPETENCIES:
    story.append(PageBreak())
story.append(Paragraph("CORE COMPETENCIES", section_style))
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
                        title="Balachandar Ramalingam - Director CV", author="Balachandar Ramalingam")
doc.build(story)
print("Generated:", OUTPUT)
