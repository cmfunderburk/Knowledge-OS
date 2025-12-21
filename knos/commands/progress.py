"""
Progress report generator.

Generates and saves PROGRESS.md report.
"""


def run_progress() -> None:
    """Generate and save progress report."""
    from reviewer.core import generate_progress_report, REPO_ROOT

    report = generate_progress_report()
    output_path = REPO_ROOT / "PROGRESS.md"
    output_path.write_text(report)

    print(report)
    print()
    print(f"Report saved to: {output_path}")
