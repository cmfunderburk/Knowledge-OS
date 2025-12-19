#!/usr/bin/env python3
"""
Progress Dashboard Generator

Outputs a markdown progress report for the study plan.
Uses shared data layer from reviewer/core.py.

Usage:
    python3 scripts/progress.py          # Print to stdout
    python3 scripts/progress.py > PROGRESS.md  # Save to file
"""

import sys
from pathlib import Path

# Add repo root to path for imports
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from reviewer.core import generate_progress_report


if __name__ == "__main__":
    print(generate_progress_report())
