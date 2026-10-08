#!/usr/bin/env python3
"""Generate the default Leadership CV (Balachandar Ramalingam LS.pdf)."""

import os
import runpy
from pathlib import Path

os.environ["CV_OUTPUT"] = "Balachandar Ramalingam LS.pdf"
os.environ["CV_PROFILE"] = "Profile Summary-Leadership.txt"
# Workday autofill fix: render Title/Company/Location/Dates on separate lines
os.environ["CV_ATS_SPLIT_EXPERIENCE"] = "1"

runpy.run_path(str(Path(__file__).with_name("build_director_cv.py")),
               run_name="__main__")
