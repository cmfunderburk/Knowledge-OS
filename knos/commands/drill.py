"""
Drill TUI launcher.

Launches the drill queue TUI for practicing due cards.
"""
import sys


def run_drill() -> None:
    """Launch the drill TUI."""
    try:
        from knos.tui.app import DrillApp
        app = DrillApp()
        app.run()
    except ImportError as e:
        print(f"Error starting drill TUI: {e}")
        print("Try running: uv run knos drill")
        sys.exit(1)
