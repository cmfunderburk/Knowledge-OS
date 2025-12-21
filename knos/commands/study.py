"""
Study TUI launcher.

Launches the main study dashboard TUI.
"""
import sys


def run_study() -> None:
    """Launch the study TUI."""
    try:
        from knos.tui.app import StudyApp
        app = StudyApp()
        app.run()
    except ImportError as e:
        print(f"Error starting TUI: {e}")
        print("Try running: uv run knos study")
        sys.exit(1)
