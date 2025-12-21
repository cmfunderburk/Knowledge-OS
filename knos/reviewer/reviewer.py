#!/usr/bin/env python3
"""
REVIEWER CLI tool for line-by-line reveal spaced repetition practice.
Wraps core business logic for interactive terminal usage.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Import core logic
from .core import (
    FOCUS_DIR,
    REPO_ROOT,
    BlockResult,
    CodeBlock,
    ParsedMarkdown,
    SessionResult,
    append_history,
    collect_due_focus_files,
    collect_focus_files,
    get_solution_key,
    load_schedule,
    parse_due_str,
    parse_markdown,
    update_schedule,
)


# ==========================================================================
# INPUT HANDLING
# ==========================================================================

def wait_for_key() -> str:
    """Wait for single keypress (y/n/s/q)."""
    try:
        import readchar
        while True:
            key = readchar.readkey().lower()
            if key in ['y', 'n', 's', 'q']:
                return key
    except ImportError:
        # Fallback to input() if readchar not available
        while True:
            try:
                response = input().strip().lower()
                if response in ['y', 'n', 's', 'q']:
                    return response
            except EOFError:
                return 'q'


# ==========================================================================
# TUI RENDERING
# ==========================================================================

def render_document_with_reveal(
    parsed: ParsedMarkdown,
    current_block_idx: int,
    current_line: int,
    current_results: list[bool],
    completed_results: list[BlockResult]
):
    """
    Render the full document with context, showing:
    - All markdown prose (headers, explanations)
    - Completed blocks: fully revealed with ✓/✗ markers
    - Current block: reveal interface with progress
    - Future blocks: placeholders
    """
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except ImportError:
        _render_document_simple(parsed, current_block_idx, current_line,
                               current_results, completed_results)
        return

    console = Console()
    console.clear()

    # Build the document with block substitutions
    result_text = parsed.raw_text
    target_blocks = parsed.target_blocks

    # Process blocks in reverse order to preserve positions
    for i in range(len(target_blocks) - 1, -1, -1):
        block = target_blocks[i]
        block_num = i + 1

        if i < current_block_idx:
            # Completed block: show full content with markers
            block_result = completed_results[i]
            replacement = _format_completed_block(block, block_result, block_num)
        elif i == current_block_idx:
            # Current block: show reveal interface
            replacement = _format_current_block(block, current_line, current_results, block_num, len(target_blocks))
        else:
            # Future block: show placeholder
            line_count = len(block.lines)
            replacement = f"```{{block.language}}\n[BLOCK {{block_num}}] {{block.language}} - {{line_count}} lines\n```"

        result_text = result_text[:block.start_pos] + replacement + result_text[block.end_pos:]

    # Render the document
    console.print(Markdown(result_text))

    # Show key hints at bottom
    console.print()
    console.print("[dim](y) knew it | (n) didn't know | (s)kip block | (q)uit[/dim]")


def _format_completed_block(block: CodeBlock, result: BlockResult, block_num: int) -> str:
    """Format a completed block with ✓/✗ markers."""
    lines = []
    lines.append(f"```{block.language}")
    lines.append(f"# BLOCK {block_num} ✓ COMPLETE")
    for i, (line, knew_it) in enumerate(zip(block.lines, result.results)):
        marker = "✓" if knew_it else "✗"
        lines.append(f"{line}  {marker}")
    lines.append("```")
    return "\n".join(lines)


def _format_current_block(
    block: CodeBlock,
    current_line: int,
    results: list[bool],
    block_num: int,
    total_blocks: int
) -> str:
    """Format the current block with reveal interface."""
    lines = []
    lines.append(f"```{block.language}")
    lines.append(f"# BLOCK {block_num} of {total_blocks} — REVEALING ({len(block.lines)} lines)")
    lines.append("")

    # Show revealed lines
    for i, (line, knew_it) in enumerate(zip(block.lines[:len(results)], results)):
        marker = "✓" if knew_it else "✗"
        lines.append(f"{line}  {marker}")

    # Show prompt for next line
    if current_line < len(block.lines):
        lines.append("")
        lines.append(f">>> Line {current_line + 1}: [y/n/s/q]")
    else:
        lines.append("")
        lines.append(">>> Block complete! Press any key to continue...")

    lines.append("```")
    return "\n".join(lines)


def _render_document_simple(
    parsed: ParsedMarkdown,
    current_block_idx: int,
    current_line: int,
    current_results: list[bool],
    completed_results: list[BlockResult]
):
    """Simple fallback rendering without rich."""
    os.system('clear' if os.name != 'nt' else 'cls')

    target_blocks = parsed.target_blocks
    result_text = parsed.raw_text

    # Process blocks in reverse order
    for i in range(len(target_blocks) - 1, -1, -1):
        block = target_blocks[i]
        block_num = i + 1

        if i < current_block_idx:
            block_result = completed_results[i]
            replacement = _format_completed_block(block, block_result, block_num)
        elif i == current_block_idx:
            replacement = _format_current_block(block, current_line, current_results, block_num, len(target_blocks))
        else:
            line_count = len(block.lines)
            replacement = f"```{block.language}\n[BLOCK {block_num}] {block.language} - {line_count} lines\n```"

        result_text = result_text[:block.start_pos] + replacement + result_text[block.end_pos:]

    print(result_text)
    print("\n(y) knew it | (n) didn't know | (s)kip block | (q)uit")


def render_session_summary(result: SessionResult, solution_path: Path):
    """Render session summary after completion."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
    except ImportError:
        _render_session_summary_simple(result, solution_path)
        return

    console = Console()
    console.print()

    content = Text()
    content.append(f"Solution: {solution_path.name}\n\n", style="bold")
    content.append(f"Lines correct: {result.correct_lines}/{result.total_lines}\n")
    content.append(f"Score: {result.score:.1f}%\n\n", style="bold")

    if result.score >= 100.0:
        content.append("Perfect! Advancing to next box.", style="green bold")
    else:
        content.append("Reset to box 0. Keep practicing!", style="yellow")

    style = "green" if result.score >= 100.0 else "yellow"
    panel = Panel(content, title="Session Complete", border_style=style)
    console.print(panel)


def _render_session_summary_simple(result: SessionResult, solution_path: Path):
    """Simple fallback session summary."""
    print(f"\n{'=' * 50}")
    print("SESSION COMPLETE")
    print('=' * 50)
    print(f"Solution: {solution_path.name}")
    print(f"Lines correct: {result.correct_lines}/{result.total_lines}")
    print(f"Score: {result.score:.1f}%")

    if result.score >= 100.0:
        print("\nPerfect! Advancing to next box.")
    else:
        print("\nReset to box 0. Keep practicing!")


# ==========================================================================
# REVEAL SESSION LOGIC
# ==========================================================================

def run_block_reveal(
    parsed: ParsedMarkdown,
    block_idx: int,
    completed_results: list[BlockResult]
) -> BlockResult:
    """Reveal one block line-by-line with self-assessment."""
    block = parsed.target_blocks[block_idx]
    lines = block.lines
    current_line = 0
    results: list[bool] = []

    while current_line < len(lines):
        render_document_with_reveal(parsed, block_idx, current_line, results, completed_results)
        key = wait_for_key()

        if key == 'y':
            results.append(True)
            current_line += 1
        elif key == 'n':
            results.append(False)
            current_line += 1
        elif key == 's':
            # Skip: mark all remaining lines as incorrect
            remaining = len(lines) - current_line
            results.extend([False] * remaining)
            current_line = len(lines)
        elif key == 'q':
            # Quit: return partial results
            return BlockResult(lines=lines, results=results, quit=True)

    # Show final state of completed block
    render_document_with_reveal(parsed, block_idx, current_line, results, completed_results)

    return BlockResult(lines=lines, results=results, quit=False)


def run_reveal_session(solution_path: Path) -> SessionResult:
    """Run a complete reveal session for one solution file."""
    text = solution_path.read_text()
    parsed = parse_markdown(text)

    if not parsed.target_blocks:
        print("No code blocks to review in this file.")
        return SessionResult(
            blocks=[], 
            total_lines=0, 
            correct_lines=0, 
            score=100.0,
            solution_path=solution_path,
            timestamp=datetime.now()
        )

    completed_results: list[BlockResult] = []

    for i, block in enumerate(parsed.target_blocks):
        result = run_block_reveal(parsed, i, completed_results)
        completed_results.append(result)

        if result.quit:
            break

        # Brief pause between blocks (press any key to continue)
        if i < len(parsed.target_blocks) - 1:
            wait_for_key()

    # Calculate totals
    total_lines = sum(len(r.lines) for r in completed_results)
    correct_lines = sum(sum(r.results) for r in completed_results)
    score = 100.0 * correct_lines / total_lines if total_lines > 0 else 100.0

    return SessionResult(
        blocks=completed_results,
        total_lines=total_lines,
        correct_lines=correct_lines,
        score=score,
        solution_path=solution_path,
        timestamp=datetime.now()
    )

def run_focus_session(files: list[Path]) -> int:
    """Run focus drills sequentially, honoring quit requests."""
    if not files:
        return 0

    queue = files[:]
    random.shuffle(queue)
    total = len(queue)

    for idx, solution_path in enumerate(queue, start=1):
        print(f"[{idx}/{total}] {solution_path.name}")
        result = run_reveal_session(solution_path)

        # Show summary and update schedule
        render_session_summary(result, solution_path)
        update_schedule(solution_path, result.score)
        append_history(result)

        # Check if user quit during session
        if result.blocks and result.blocks[-1].quit:
            return 2

        # Prompt to continue (except after last solution)
        if idx < total:
            try:
                from rich.console import Console
                console = Console()
                console.print("\n[dim]Press any key for next solution (q to quit)...[/dim]")
            except ImportError:
                print("\nPress any key for next solution (q to quit)...")

            key = wait_for_key()
            if key == 'q':
                return 2

    return 0


# ==========================================================================
# CLI ENTRY POINT
# ==========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Line-by-line reveal spaced repetition tool"
    )
    parser.add_argument(
        "solution",
        nargs="?",
        help="Path to solution file"
    )
    parser.add_argument(
        "--focus",
        action="store_true",
        help="Drill all solutions in solutions/focus/ (random order)"
    )
    parser.add_argument(
        "--drill-due",
        action="store_true",
        help="Drill only due solutions from solutions/focus/"
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

    args = parser.parse_args()

    # --due-json: output due info as JSON for scripts
    if args.due_json:
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

    # --due: human-readable due list
    if args.due:
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

    # --drill-due: only review due cards from focus/
    if args.drill_due:
        due_files = collect_due_focus_files()
        if not due_files:
            print("Nothing due in solutions/focus/! All caught up.")
            return 0
        print(f"Drilling {len(due_files)} due card(s) from focus/\n")
        return run_focus_session(due_files)

    # --focus: review all cards in focus/ (shuffled)
    if args.focus:
        focus_files = collect_focus_files()
        if not focus_files:
            print(f"No readable solutions found in {FOCUS_DIR}")
            return 1
        print(f"Drilling {len(focus_files)} solution(s) from focus/\n")
        return run_focus_session(focus_files)

    # Single solution mode
    if not args.solution:
        print("Usage: python3 reviewer.py <solution_path>")
        print("   or: python3 reviewer.py --focus")
        print("   or: python3 reviewer.py --drill-due")
        print("\nExample: python3 reviewer.py solutions/focus/quick_sort_pythonic.md")
        return 1

    solution_path = Path(args.solution)

    # Handle relative paths (resolve from repo root, not package directory)
    if not solution_path.is_absolute():
        solution_path = REPO_ROOT / solution_path

    if not solution_path.exists():
        print(f"Error: File not found: {solution_path}")
        return 1

    # Run the reveal session
    result = run_reveal_session(solution_path)

    # Show summary and update schedule
    render_session_summary(result, solution_path)
    update_schedule(solution_path, result.score)
    append_history(result)

    # Exit code based on score
    return 0 if result.score >= 100.0 else 1


if __name__ == "__main__":
    sys.exit(main())