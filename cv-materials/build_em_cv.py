#!/usr/bin/env python3
"""Generate the Engineering Manager CV with its positioning title."""

import os
import runpy
from pathlib import Path

os.environ["CV_OUTPUT"] = "Balachandar Ramalingam EM.pdf"
os.environ["CV_PROFILE"] = "Profile Summary-Leadership.txt"
os.environ["CV_TITLE_LINE"] = (
    "Associate Director of Engineering &nbsp;|&nbsp; Enterprise AI &amp; Platforms "
    "&nbsp;|&nbsp; GCC Leadership"
)
# Workday autofill fix: render Title/Company/Location/Dates on separate lines
os.environ["CV_ATS_SPLIT_EXPERIENCE"] = "1"

runpy.run_path(str(Path(__file__).with_name("build_director_cv.py")),
               run_name="__main__")
