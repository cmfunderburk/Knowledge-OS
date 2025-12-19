"""
Core business logic for the Knowledge OS spaced-repetition system.
Contains data models, parsing logic, and schedule management.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml

# ==========================================================================
# CONSTANTS & CONFIGURATION
# ==========================================================================
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
SOLUTIONS_ROOT = REPO_ROOT / "solutions"
FOCUS_DIR = SOLUTIONS_ROOT / "focus"
PLAN_DIR = REPO_ROOT / "plan"
SCHEDULE_PATH = PLAN_DIR / "schedule.json"
HISTORY_PATH = BASE_DIR / "history.jsonl"
TODO_FILE = PLAN_DIR / "todo.md"
STUDY_CONFIG_PATH = PLAN_DIR / "study_config.yaml"
PRIORITY_SHIFT_PATH = PLAN_DIR / "priority_shift.md"

# Default domain rotation (used if no config file)
DEFAULT_DOMAIN_ROTATION = {
    0: "Domain 1",
    1: "Domain 2",
    2: "Domain 3",
    3: "Domain 4",
    4: "Review",
    5: "Off",
    6: "Off",
}

# Default phases (used if no config file)
DEFAULT_PHASES = [
    {"num": 1, "name": "Phase 1", "status": "Not Started"},
    {"num": 2, "name": "Phase 2", "status": "Not Started"},
    {"num": 3, "name": "Phase 3", "status": "Not Started"},
]


def load_study_config() -> dict:
    """
    Load study configuration from study_config.yaml.

    Returns empty dict if file doesn't exist (defaults will be used).
    """
    if not STUDY_CONFIG_PATH.exists():
        return {}
    try:
        with open(STUDY_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return {}


def get_domain_rotation() -> dict[int, str]:
    """Get domain rotation from config or use defaults."""
    config = load_study_config()
    domains = config.get("domains")
    if domains:
        # Convert string keys to int if needed
        return {int(k): v for k, v in domains.items()}
    return DEFAULT_DOMAIN_ROTATION.copy()


def get_current_phase() -> dict:
    """Get current phase info from config."""
    config = load_study_config()
    return config.get("current_phase", {"name": "Phase 0", "description": "Foundations"})


def get_future_phases() -> list[dict]:
    """Get future phases from config or use defaults."""
    config = load_study_config()
    return config.get("phases", DEFAULT_PHASES)


def get_priority_shift_config() -> dict:
    """Get priority shift config."""
    config = load_study_config()
    return config.get("priority_shift", {"enabled": False})

# Leitner box spaced repetition settings
# Box 0 = new/reset, Box 6 = mastered (max)
LEITNER_INTERVALS = [
    timedelta(hours=1),    # Box 0: new or reset after failure
    timedelta(hours=4),    # Box 1
    timedelta(days=1),     # Box 2
    timedelta(days=3),     # Box 3
    timedelta(days=7),     # Box 4
    timedelta(days=14),    # Box 5
    timedelta(days=30),    # Box 6: mastered
]
MAX_BOX = len(LEITNER_INTERVALS) - 1

# Regex for fenced code blocks: ```lang\ncontent\n```
CODE_BLOCK_PATTERN = re.compile(
    r'^```(\w*)\n(.*?)^```',
    re.MULTILINE | re.DOTALL
)

INFO_MARKER = "<!-- INFO -->"


# ==========================================================================
# DATA STRUCTURES
# ==========================================================================

@dataclass
class CodeBlock:
    """A fenced code block extracted from markdown."""
    language: str
    content: str
    lines: list[str]
    start_pos: int
    end_pos: int
    is_target: bool  # False if preceded by <!-- INFO -->


@dataclass
class ParsedMarkdown:
    """Result of parsing a markdown file."""
    raw_text: str
    blocks: list[CodeBlock]
    target_blocks: list[CodeBlock]


@dataclass
class BlockResult:
    """Result of revealing one block."""
    lines: list[str]
    results: list[bool]  # True = knew it (y), False = didn't (n)
    quit: bool = False


@dataclass
class SessionResult:
    """Result of a complete reveal session."""
    blocks: list[BlockResult]
    total_lines: int
    correct_lines: int
    score: float
    solution_path: Path = None  # Added for history logging
    timestamp: datetime = None  # Added for history logging

    def to_dict(self):
        """Convert to dictionary for logging."""
        return {
            "solution": str(self.solution_path) if self.solution_path else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "total_lines": self.total_lines,
            "correct_lines": self.correct_lines,
            "score": self.score
        }


# ==========================================================================
# MARKDOWN PARSING
# ==========================================================================

def parse_markdown(text: str) -> ParsedMarkdown:
    """
    Extract fenced code blocks from markdown text.

    Blocks preceded by <!-- INFO --> (within 50 chars) are marked as non-targets.
    Returns ParsedMarkdown with all blocks and filtered target_blocks.
    """
    blocks = []

    for match in CODE_BLOCK_PATTERN.finditer(text):
        language = match.group(1) or "text"
        content = match.group(2).rstrip('\n')
        start_pos = match.start()
        end_pos = match.end()

        # Check for <!-- INFO --> marker within 50 chars before fence
        prefix_start = max(0, start_pos - 50)
        prefix = text[prefix_start:start_pos]
        is_target = INFO_MARKER not in prefix

        # Split content into lines for line-by-line reveal
        lines = content.split('\n') if content else []

        blocks.append(CodeBlock(
            language=language,
            content=content,
            lines=lines,
            start_pos=start_pos,
            end_pos=end_pos,
            is_target=is_target
        ))

    target_blocks = [b for b in blocks if b.is_target]

    return ParsedMarkdown(
        raw_text=text,
        blocks=blocks,
        target_blocks=target_blocks
    )


# ==========================================================================
# SCHEDULE MANAGEMENT
# ==========================================================================

def get_solution_key(solution_path: Path) -> str:
    """Get the schedule key for a solution (relative path from solutions dir)."""
    try:
        return str(solution_path.relative_to(SOLUTIONS_ROOT))
    except ValueError:
        return solution_path.name


def load_schedule() -> dict:
    """Load schedule.json, create empty dict if missing."""
    if not SCHEDULE_PATH.exists():
        return {}
    try:
        with open(SCHEDULE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_schedule(schedule: dict):
    """Save schedule.json."""
    with open(SCHEDULE_PATH, 'w') as f:
        json.dump(schedule, f, indent=2)

def update_schedule(solution_path: Path, score: float):
    """Update schedule after session completion using Leitner box system."""
    schedule = load_schedule()
    key = get_solution_key(solution_path)
    now = datetime.now()

    current = schedule.get(key, {})
    old_box = current.get("box", 0)

    if score >= 100.0:
        # Perfect: advance to next box (capped at MAX_BOX)
        new_box = min(old_box + 1, MAX_BOX)
    else:
        # Imperfect: reset to box 0
        new_box = 0

    # Calculate next due datetime
    interval = LEITNER_INTERVALS[new_box]
    next_due = now + interval

    schedule[key] = {
        "box": new_box,
        "next_due": next_due.isoformat(timespec="minutes"),
        "last_score": score,
        "last_reviewed": now.isoformat(timespec="minutes"),
    }

    save_schedule(schedule)

def parse_due_str(s: str) -> datetime:
    """Parse ISO datetime string, return datetime.min if invalid."""
    if not s:
        return datetime.min
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
             # Convert valid timezone-aware object to local timezone, then make naive
             return dt.astimezone().replace(tzinfo=None)
        return dt
    except ValueError:
        return datetime.min


# ==========================================================================
# FILE COLLECTION
# ==========================================================================

def collect_all_solutions() -> list[Path]:
    """Return all markdown solution files recursively."""
    if not SOLUTIONS_ROOT.exists():
        return []
    
    files = []
    for path in SOLUTIONS_ROOT.rglob("*.md"):
        if path.name.startswith("."):
            continue
        files.append(path.resolve())
        
    return sorted(files, key=lambda p: str(p.relative_to(SOLUTIONS_ROOT)))

def collect_focus_files() -> list[Path]:
    """Return readable, non-hidden markdown files in the focus directory (recursive)."""
    if not FOCUS_DIR.exists() or not FOCUS_DIR.is_dir():
        return []

    files: list[Path] = []
    for path in FOCUS_DIR.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.is_file() and os.access(path, os.R_OK):
            files.append(path.resolve())
    return sorted(files, key=lambda p: p.name.lower())


def collect_due_focus_files() -> list[Path]:
    """
    Get files from solutions/focus/ that are due for review.

    Returns files that are either:
    1. In box 0 (failed - always available for immediate re-drill)
    2. Due or overdue (in schedule with next_due <= now)
    3. Never practiced (not in schedule)

    Files are sorted by priority: box 0 first, then overdue, then unscheduled.
    """
    if not FOCUS_DIR.exists() or not FOCUS_DIR.is_dir():
        return []

    schedule = load_schedule()
    now = datetime.now()

    box_zero: list[tuple[Path, datetime]] = []  # (path, last_reviewed)
    overdue: list[tuple[Path, datetime]] = []  # (path, due_datetime)
    unscheduled: list[Path] = []

    for path in FOCUS_DIR.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if not path.is_file() or not os.access(path, os.R_OK):
            continue

        key = get_solution_key(path)
        entry = schedule.get(key)

        if entry is None:
            # Never practiced
            unscheduled.append(path)
        else:
            box = entry.get("box", 0)

            if box == 0:
                # Box 0 items are always due (failed cards for immediate re-drill)
                last_reviewed = parse_due_str(entry.get("last_reviewed", ""))
                box_zero.append((path, last_reviewed))
            else:
                next_due_str = entry.get("next_due", "")
                next_due = parse_due_str(next_due_str)
                if next_due <= now:
                    overdue.append((path, next_due))
                # else: not due yet, skip

    # Sort box 0 by last reviewed (least recent first - practice oldest failures first)
    box_zero.sort(key=lambda x: x[1])

    # Sort overdue by date (oldest first)
    overdue.sort(key=lambda x: x[1])

    # Combine: box 0 first (failed), then overdue, then unscheduled
    result = [p for p, _ in box_zero] + [p for p, _ in overdue] + unscheduled
    return result


# ==========================================================================
# LOGGING
# ==========================================================================

def append_history(session_result: SessionResult):
    """Log session result to history.jsonl."""
    entry = session_result.to_dict()
    # Add current timestamp if missing
    if not entry.get("timestamp"):
        entry["timestamp"] = datetime.now().isoformat()
    
    with open(HISTORY_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ==========================================================================
# TODO / SPRINT PARSING
# ==========================================================================

def parse_todo_tasks(path: Path = None) -> tuple[int, int, list[str]]:
    """
    Parse todo file and return (total, completed, unchecked_task_texts).
    
    Args:
        path: Path to todo file. Defaults to TODO_FILE.
    
    Returns:
        (total_tasks, completed_tasks, list_of_unchecked_task_texts)
    """
    if path is None:
        path = TODO_FILE
    
    if not path.exists():
        return 0, 0, []
    
    try:
        with open(path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]

        total = sum(1 for line in lines if line.startswith('* ['))
        completed = sum(1 for line in lines if line.startswith('* [x]'))
        unchecked = [
            line.replace('* [ ]', '', 1).strip()
            for line in lines
            if line.startswith('* [ ]')
        ]
        return total, completed, unchecked
    except (IOError, OSError):
        return 0, 0, []


def parse_sprints(path: Path = None) -> list[dict]:
    """
    Parse todo.md to extract sprint progress.
    
    Returns list of dicts: {num, name, done, total, status}
    """
    if path is None:
        path = TODO_FILE
        
    if not path.exists():
        return []

    content = path.read_text()
    
    # Format: ### 🛠 Sprint 1: Setup & Logic Foundations
    sprint_pattern = re.compile(r"^### .* Sprint (\d+):\s*(.+)$", re.MULTILINE)
    
    matches = list(sprint_pattern.finditer(content))
    if not matches:
        return []
    
    sprints = []
    for i, match in enumerate(matches):
        sprint_num = int(match.group(1))
        sprint_name = match.group(2).strip()
        
        # Get content between this sprint and next (or end)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end]
        
        # Count checkboxes
        done = len(re.findall(r"^\s*\*\s*\[x\]", section, re.MULTILINE | re.IGNORECASE))
        not_done = len(re.findall(r"^\s*\*\s*\[ \]", section, re.MULTILINE))
        total = done + not_done
        
        # Determine status
        if done == 0:
            status = "not-started"
        elif done == total:
            status = "complete"
        else:
            status = "in-progress"
        
        sprints.append({
            "num": sprint_num,
            "name": sprint_name,
            "done": done,
            "total": total,
            "status": status,
        })
    
    return sprints


def get_sprint_progress() -> list[dict]:
    """
    Get sprint progress from todo.md.
    
    Returns: [
        {"num": 1, "name": "Setup", "done": 5, "total": 5, "status": "complete"},
        {"num": 2, "name": "Logic", "done": 3, "total": 7, "status": "in-progress"},
        ...
    ]
    """
    return parse_sprints(TODO_FILE)


def get_overall_progress() -> tuple[int, int]:
    """
    Get overall progress across all sprints.
    
    Returns: (total_done, total_tasks)
    """
    sprints = get_sprint_progress()
    done = sum(s["done"] for s in sprints)
    total = sum(s["total"] for s in sprints)
    return done, total


# ==========================================================================
# DASHBOARD DATA FUNCTIONS
# ==========================================================================

def read_priority_shift_metadata(path: Path = None) -> dict[str, str] | None:
    """
    Read priority shift metadata from schedules-llm/priority_shift.md.

    Returns dict with optional keys: status, focus, ratio.
    If file missing/unreadable, returns None.
    """
    if path is None:
        path = PRIORITY_SHIFT_PATH
    if not path.exists():
        return None
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return None

    def _grab(label: str) -> str | None:
        m = re.search(
            rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        return m.group(1).strip() if m else None

    return {
        "status": _grab("Status") or "",
        "focus": _grab("Focus") or "",
        "ratio": _grab("Ratio") or "",
    }


def is_priority_shift_active(meta: dict[str, str] | None = None) -> bool:
    """
    Determine whether the priority shift is active.

    Logic:
    - No file => inactive.
    - If a Status line exists, Active iff it starts with "active" (case-insensitive).
    - If no Status line, treat existence as active (backward compatible).
    """
    if meta is None:
        meta = read_priority_shift_metadata()
    if meta is None:
        return False
    status = (meta.get("status") or "").strip().lower()
    if status:
        return status.startswith("active")
    return True


def get_todays_domain() -> tuple[str, str | None]:
    """
    Get today's scheduled domain.

    Checks for active priority shift first (from study_config.yaml).
    If current phase is incomplete, returns phase as the domain with a note
    about what the scheduled domain would be.

    Returns: (display_domain, override_note or None)
    """
    domain_rotation = get_domain_rotation()
    current_phase = get_current_phase()
    priority_shift = get_priority_shift_config()

    # 1. Check for Priority Shift (from config)
    if priority_shift.get("enabled"):
        shift_name = priority_shift.get("name", "Priority Shift")
        ratio = (priority_shift.get("ratio") or "").rstrip(".")
        override = "(Priority Shift Active)"
        if ratio:
            override = f"(Priority Shift Active — {ratio})"
        return shift_name, override

    weekday = dt.date.today().weekday()
    scheduled_domain = domain_rotation.get(weekday, "Unknown")

    # Check if current phase is complete
    total, completed, _ = parse_todo_tasks(TODO_FILE)
    if total > 0 and completed < total:
        phase_name = current_phase.get("name", "Current Phase")
        phase_desc = current_phase.get("description", "")
        display = f"{phase_name} - {phase_desc}" if phase_desc else phase_name
        return display, f"(Would be: {scheduled_domain})"

    return scheduled_domain, None


def get_next_task() -> str | None:
    """
    Get the first unchecked task from todo.md.

    Returns: Task text or None if all complete.
    """
    priority_shift = get_priority_shift_config()
    if priority_shift.get("enabled"):
        shift_name = priority_shift.get("name", "Priority shift")
        return f"{shift_name} active — follow milestones"
    _, _, unchecked = parse_todo_tasks(TODO_FILE)
    return unchecked[0] if unchecked else None


def get_reviewer_summary() -> dict:
    """
    Get summary statistics for the reviewer system.
    
    Returns: {
        "box_zero": int,       # Failed cards (immediate re-drill)
        "overdue": int,        # Past due date
        "due_now": int,        # Due within the hour
        "never_practiced": int,# Not in schedule
        "total_focus": int,    # Total cards in focus/
        "last_practiced": str | None,  # ISO datetime string
    }
    """
    schedule = load_schedule()
    focus_files = collect_focus_files()
    now = datetime.now()
    
    box_zero = 0
    overdue = 0
    due_now = 0
    scheduled_keys = set()
    last_practiced = None
    
    for key, data in schedule.items():
        scheduled_keys.add(key)
        box = data.get("box", 0)
        next_due = parse_due_str(data.get("next_due"))
        last_rev = data.get("last_reviewed")
        
        if box == 0:
            box_zero += 1
        elif next_due != datetime.min:
            if next_due < now - timedelta(hours=1):
                overdue += 1
            elif next_due <= now:
                due_now += 1
        
        if last_rev:
            if last_practiced is None or last_rev > last_practiced:
                last_practiced = last_rev
    
    # Never practiced = in focus/ but not in schedule
    focus_keys = {get_solution_key(f) for f in focus_files}
    never_practiced = len(focus_keys - scheduled_keys)
    
    return {
        "box_zero": box_zero,
        "overdue": overdue,
        "due_now": due_now,
        "never_practiced": never_practiced,
        "total_focus": len(focus_files),
        "last_practiced": last_practiced,
    }


def get_drill_queue() -> list[tuple[Path, dict]]:
    """
    Get prioritized list of cards ready to drill.
    
    Priority order:
    1. Box 0 (failed) - most urgent
    2. Overdue (oldest first)
    3. Due now
    4. Never practiced
    
    Returns: [(path, metadata_dict), ...]
        where metadata_dict has: box, status, due_info
    """
    if not FOCUS_DIR.exists() or not FOCUS_DIR.is_dir():
        return []

    schedule = load_schedule()
    now = datetime.now()

    box_zero: list[tuple[Path, datetime, dict]] = []
    overdue: list[tuple[Path, datetime, dict]] = []
    due_now_list: list[tuple[Path, datetime, dict]] = []
    unscheduled: list[tuple[Path, dict]] = []

    for path in FOCUS_DIR.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if not path.is_file() or not os.access(path, os.R_OK):
            continue

        key = get_solution_key(path)
        entry = schedule.get(key)

        if entry is None:
            # Never practiced
            meta = {"box": None, "status": "new", "due_info": "never practiced"}
            unscheduled.append((path, meta))
        else:
            box = entry.get("box", 0)
            next_due_str = entry.get("next_due", "")
            next_due = parse_due_str(next_due_str)
            last_reviewed = parse_due_str(entry.get("last_reviewed", ""))

            if box == 0:
                # Box 0 items are always due (failed cards)
                meta = {"box": 0, "status": "failed", "due_info": "failed"}
                if last_reviewed != datetime.min:
                    delta = now - last_reviewed
                    meta["due_info"] = format_time_delta(delta) + " ago"
                box_zero.append((path, last_reviewed, meta))
            elif next_due != datetime.min and next_due <= now:
                delta = now - next_due
                if delta > timedelta(hours=1):
                    meta = {"box": box, "status": "overdue", "due_info": f"overdue {format_time_delta(delta)}"}
                    overdue.append((path, next_due, meta))
                else:
                    meta = {"box": box, "status": "due", "due_info": "due now"}
                    due_now_list.append((path, next_due, meta))
            # else: not due yet, skip

    # Sort each group
    box_zero.sort(key=lambda x: x[1])  # oldest failure first
    overdue.sort(key=lambda x: x[1])   # oldest overdue first
    due_now_list.sort(key=lambda x: x[1])
    unscheduled.sort(key=lambda x: x[0].name.lower())

    # Combine into final list
    result = []
    for path, _, meta in box_zero:
        result.append((path, meta))
    for path, _, meta in overdue:
        result.append((path, meta))
    for path, _, meta in due_now_list:
        result.append((path, meta))
    for path, meta in unscheduled:
        result.append((path, meta))
    
    return result


def format_time_delta(delta: timedelta) -> str:
    """Format a timedelta into a human-readable string."""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 0:
        return "now"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d" if hours == 0 else f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h" if minutes == 0 else f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "now"


def ascii_progress_bar(done: int, total: int, width: int = 12) -> str:
    """Generate an ASCII progress bar using block characters."""
    if total == 0:
        return "░" * width
    pct = done / total
    filled = int(pct * width)
    empty = width - filled
    return "█" * filled + "░" * empty


def generate_progress_report() -> str:
    """
    Generate a markdown progress report.
    
    This consolidates what scripts/progress.py does.
    Returns: Markdown string.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    day_name = now.strftime("%A, %B %d, %Y")
    
    lines = [
        "# Progress Dashboard",
        "",
        f"*Generated: {today_str}*",
        "",
    ]
    
    # === TODAY SECTION ===
    domain, override = get_todays_domain()
    next_task = get_next_task()
    
    lines.extend([
        "## Today",
        "",
    ])
    
    if override:
        lines.append(f"- **Domain:** {domain} *{override}*")
    else:
        lines.append(f"- **Domain:** {domain}")
    
    if next_task:
        # Truncate if very long
        task_display = next_task[:80] + "..." if len(next_task) > 80 else next_task
        lines.append(f"- **Next Task:** {task_display}")
    else:
        lines.append("- **Next Task:** All tasks complete! 🎉")
    
    lines.extend([
        "",
        f"*{day_name}*",
        "",
    ])

    # === PRIORITY SHIFT CHECK ===
    priority_shift = get_priority_shift_config()
    if priority_shift.get("enabled"):
        shift_name = priority_shift.get("name", "Priority Shift")
        focus = priority_shift.get("focus", "")
        ratio = priority_shift.get("ratio", "")
        lines.append(f"## 🚨 {shift_name.upper()} ACTIVE")
        lines.append("")
        if focus:
            lines.append(f"**Focus:** {focus}")
        if ratio:
            lines.append(f"**Ratio:** {ratio}")
        milestones_file = priority_shift.get("milestones_file")
        if milestones_file:
            lines.append(f"**Status:** See `{milestones_file}` for milestones.")
        lines.append("")

    # === CURRENT PHASE: SPRINTS ===
    current_phase = get_current_phase()
    phase_name = current_phase.get("name", "Current Phase")
    phase_desc = current_phase.get("description", "")
    phase_title = f"{phase_name}: {phase_desc}" if phase_desc else phase_name
    lines.extend([
        f"## {phase_title}",
        "",
    ])
    
    sprints = get_sprint_progress()
    if sprints:
        lines.extend([
            "| Sprint | Focus | Progress |",
            "|--------|-------|----------|",
        ])
        for s in sprints:
            bar = ascii_progress_bar(s["done"], s["total"])
            check = " ✅" if s["status"] == "complete" else ""
            lines.append(f"| Sprint {s['num']} | {s['name']} | `{bar}` {s['done']}/{s['total']}{check} |")
    else:
        lines.append("*No sprint data found in todo.md*")
    
    lines.append("")
    
    # Overall progress
    done, total = get_overall_progress()
    if total > 0:
        pct = (done / total) * 100
        overall_bar = ascii_progress_bar(done, total)
        lines.append(f"**Overall:** {done}/{total} ({pct:.0f}%) `{overall_bar}`")
        lines.append("")
    
    # === REVIEWER STATUS ===
    lines.extend([
        "## Reviewer Status",
        "",
    ])
    
    summary = get_reviewer_summary()
    
    lines.extend([
        "| Priority | Count | Description |",
        "|----------|-------|-------------|",
        f"| 🔴 Failed (Box 0) | {summary['box_zero']} | Immediate re-drill needed |",
        f"| 🟠 Overdue | {summary['overdue']} | Past scheduled review |",
        f"| 🟡 Due Now | {summary['due_now']} | Due within the hour |",
        f"| ⚪ Never Practiced | {summary['never_practiced']} | New cards in focus/ |",
        "",
        f"**Total in focus/:** {summary['total_focus']} cards",
    ])
    
    if summary["last_practiced"]:
        lines.append(f"**Last practiced:** {summary['last_practiced'][:10]}")
    
    lines.append("")
    
    # === READY TO DRILL ===
    drill_queue = get_drill_queue()
    
    lines.extend([
        "## Ready to Drill",
        "",
    ])
    
    if drill_queue:
        lines.extend([
            "| # | Card | Box | Status |",
            "|---|------|-----|--------|",
        ])
        
        display_count = min(8, len(drill_queue))
        for i in range(display_count):
            path, meta = drill_queue[i]
            name = path.stem
            if len(name) > 25:
                name = name[:22] + "..."
            
            box_str = "—" if meta["box"] is None else f"Box {meta['box']}"
            lines.append(f"| {i+1} | `{name}` | {box_str} | {meta['due_info']} |")
        
        if len(drill_queue) > display_count:
            remaining = len(drill_queue) - display_count
            lines.append("")
            lines.append(f"*Showing top {display_count} of {len(drill_queue)} due cards*")
    else:
        lines.append("✅ **All caught up!** No cards due for review.")
    
    lines.append("")
    
    # === FUTURE PHASES ===
    future_phases = get_future_phases()
    if future_phases:
        lines.extend([
            "## Future Phases",
            "",
            "| Phase | Name | Status |",
            "|-------|------|--------|",
        ])
        for phase in future_phases:
            num = phase.get("num", "?")
            name = phase.get("name", "Unnamed")
            status = phase.get("status", "Not Started")
            lines.append(f"| Phase {num} | {name} | {status} |")
        lines.extend([
            "",
            "*(Tracking not yet implemented)*",
            "",
        ])
    
    return "\n".join(lines)
