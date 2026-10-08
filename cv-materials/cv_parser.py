"""
cv_parser.py — Parse structured plain-text CV files for ReportLab build scripts.

.txt file format:
  ## SUMMARY
  Paragraph with **bold** markers and Unicode dashes (— –).

  ## COMPETENCIES
  **Term1** • **Term2** • ...

  ## EXPERIENCE

  ### Job Title — Company
  Location | Start – End
  - Bullet with **bold** keywords

  ## SKILLS
  - **Category**: comma-separated values

  ## CERTIFICATIONS
  - Certification name

  ## EDUCATION
  **Degree** — Institution, Year
"""

import re
from pathlib import Path
from typing import Union


def _rl(text: str) -> str:
    """Convert plain-text with **markers** to ReportLab-safe HTML markup."""
    text = text.replace("&", "&amp;")                          # escape & first
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)       # **bold**
    text = text.replace("—", "&mdash;")
    text = text.replace("–", "&ndash;")
    return text


def parse_cv(path: Union[str, Path]) -> dict:
    """
    Parse a structured CV .txt file.

    Returns dict with:
      summary       str  — ReportLab markup
      competencies  str  — ReportLab markup
      experience    list of {header, meta, bullets}
      skills        list of (label_rl, value_rl) tuples
      certifications list of str
      education     str
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()

    data: dict = {
        "summary": "",
        "summary_paragraphs": [],
        "competencies": "",
        "experience": [],
        "skills": [],
        "certifications": [],
        "education": "",
    }

    section = None
    current_role = None
    summary_break = False

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()

        if s.startswith("## "):
            section = s[3:].strip().upper()
            current_role = None
            continue

        if not s:
            if section == "SUMMARY":
                summary_break = True
            continue

        if section == "SUMMARY":
            data["summary"] += (" " if data["summary"] else "") + _rl(s)
            if summary_break or not data["summary_paragraphs"]:
                data["summary_paragraphs"].append(_rl(s))
            else:
                data["summary_paragraphs"][-1] += " " + _rl(s)
            summary_break = False

        elif section == "COMPETENCIES":
            data["competencies"] += (" " if data["competencies"]
                                     else "") + _rl(s)

        elif section == "EXPERIENCE":
            if s.startswith("### "):
                header = s[4:].strip()
                title, separator, company = header.rpartition(" — ")
                current_role = {
                    "header": _rl(header),
                    "title": _rl(title if separator else header),
                    "company": _rl(company if separator else ""),
                    "meta": "",
                    "location": "",
                    "dates": "",
                    "bullets": [],
                }
                data["experience"].append(current_role)
            elif current_role is not None:
                if s.startswith("#### "):
                    # sub-section header — stored with sentinel prefix for renderers
                    current_role["bullets"].append(
                        "__SUB__:" + _rl(s[5:].strip()))
                elif s.startswith("- "):
                    current_role["bullets"].append(_rl(s[2:]))
                elif "|" in s:
                    parts = [p.strip() for p in s.split("|", 1)]
                    current_role["meta"] = " &nbsp;|&nbsp; ".join(
                        _rl(p) for p in parts)
                    current_role["location"] = _rl(parts[0])
                    current_role["dates"] = _rl(
                        parts[1] if len(parts) > 1 else "")

        elif section in ("SKILLS", "TECHNICAL SKILLS",
                         "CORE COMPETENCIES",
                         "CORE COMPETENCIES & TECHNICAL SKILLS"):
            if s.startswith("- ") and ":" in s:
                content = s[2:]
                ci = content.index(":")
                label_raw, value_raw = content[:ci].strip(
                ), content[ci + 1:].strip()
                data["skills"].append((_rl(label_raw), _rl(value_raw)))

        elif section == "CERTIFICATIONS":
            if s.startswith("- "):
                data["certifications"].append(_rl(s[2:]))

        elif section == "EDUCATION":
            if s:
                data["education"] = _rl(s)

    return data
