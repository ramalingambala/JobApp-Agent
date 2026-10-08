#!/usr/bin/env python3
"""Generate the Philips DXR-targeted Director / Software R&D Leadership CV."""

import os
import runpy
from pathlib import Path

os.environ["CV_OUTPUT"] = "Balachandar Ramalingam LS DXR.pdf"
os.environ["CV_PROFILE"] = "Profile Summary-Leadership-DXR.txt"
os.environ["CV_ATS_SPLIT_EXPERIENCE"] = "1"
os.environ["CV_TITLE_LINE"] = (
    "Director, Software Engineering &amp; R&amp;D &nbsp;|&nbsp; AI-First Platform "
    "Transformation &nbsp;|&nbsp; Healthcare &amp; Regulated Systems"
)

runpy.run_path(str(Path(__file__).with_name("build_director_cv.py")),
               run_name="__main__")
