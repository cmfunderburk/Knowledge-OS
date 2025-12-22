#!/usr/bin/env python3
"""
REVIEWER CLI tool - non-interactive query modes.

For interactive drilling, use: knos drill

This module provides command-line query modes for scripting and inspection:
  --due       Human-readable list of due cards
  --due-json  JSON output for script consumption
  --summary   Mastery status overview
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .core import (
    collect_due_focus_files,
    get_reviewer_summary,
    get_solution_key,
    load_schedule,
    parse_due_str,
)


def cmd_due_json() -> int:
    """Output due info as JSON for scripts."""
    due_files = collect_due_focus_files()
    schedule = load_schedule()
    now = datetime.now()

    box_zero = []
    overdue = []
    never_practiced = []

    for path in due_files:
        key = get_solution_key(path)
        entry = schedule.get(key)
        if entry is None:
            never_practiced.append(key)
        else:
            box = entry.get("box", 0)
            if box == 0:
                box_zero.append(key)
            else:
                next_due_str = entry.get("next_due", "")
                next_due = parse_due_str(next_due_str)
                if next_due <= now:
                    overdue.append(key)

    output = {
        "datetime": now.isoformat(timespec="minutes"),
        "box_zero": box_zero,
        "overdue": overdue,
        "due_now": [],
        "never_practiced": never_practiced,
        "total_due": len(box_zero) + len(overdue),
    }
    print(json.dumps(output, indent=2))
    return 0


def cmd_due() -> int:
    """Human-readable due list."""
    due_files = collect_due_focus_files()
    if not due_files:
        print("Nothing due in solutions/focus/! All caught up.")
        return 0

    schedule = load_schedule()

    print(f"Due for review ({len(due_files)} cards):\n")

    for path in due_files:
        key = get_solution_key(path)
        entry = schedule.get(key)

        if entry is None:
            print(f"  • {path.name} (never practiced)")
        else:
            box = entry.get("box", 0)
            last_score = entry.get("last_score", 0)
            print(f"  • {path.name} (box {box}, last: {last_score:.0f}%)")

    return 0


def cmd_summary() -> int:
    """Print mastery status overview."""
    summary = get_reviewer_summary()

    print("Reviewer Status")
    print("=" * 40)

    if summary["box_zero"] > 0:
        print(f"  Box 0 (failed):    {summary['box_zero']}")
    if summary["overdue"] > 0:
        print(f"  Overdue:           {summary['overdue']}")
    if summary["due_now"] > 0:
        print(f"  Due now:           {summary['due_now']}")
    if summary["never_practiced"] > 0:
        print(f"  Never practiced:   {summary['never_practiced']}")

    total_due = summary["box_zero"] + summary["overdue"] + summary["due_now"]
    if total_due == 0 and summary["never_practiced"] == 0:
        print("  All caught up!")

    print()
    print(f"  Total in focus/:   {summary['total_focus']}")

    if summary["last_practiced"]:
        print(f"  Last practiced:    {summary['last_practiced'][:10]}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Reviewer query tool (for interactive drilling, use: knos drill)"
    )
    parser.add_argument(
        "--due",
        action="store_true",
        help="Show solutions due for review"
    )
    parser.add_argument(
        "--due-json",
        action="store_true",
        help="Output due solutions as JSON (for script consumption)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show mastery status overview"
    )

    args = parser.parse_args()

    if args.due_json:
        return cmd_due_json()

    if args.due:
        return cmd_due()

    if args.summary:
        return cmd_summary()

    # No flags: show help
    parser.print_help()
    print("\nFor interactive drilling, use: knos drill")
    return 0


if __name__ == "__main__":
    sys.exit(main())
