#!/usr/bin/env python3
"""Generate the Visa-targeted leadership CV."""

import os
import runpy
from pathlib import Path

os.environ["CV_OUTPUT"] = "Balachandar Ramalingam LS Visa.pdf"
os.environ["CV_PROFILE"] = "Profile Summary-Leadership-Visa.txt"
os.environ["CV_ATS_SPLIT_EXPERIENCE"] = "1"
os.environ["CV_TITLE_LINE"] = (
    "Director, Software Engineering &nbsp;|&nbsp; Data Platforms &amp; GenAI "
    "&nbsp;|&nbsp; Global Engineering Leadership"
)

runpy.run_path(str(Path(__file__).with_name("build_director_cv.py")),
               run_name="__main__")
