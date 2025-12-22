"""
Textual application entry points for the KnOS TUI.

Provides three app classes that can be run independently:
- StudyApp: Full dashboard with drill queue, progress, and reader access
- DrillApp: Minimal app that jumps directly to the drill queue
- ReaderApp: Minimal app that jumps directly to material selection
"""
from textual.app import App
from textual.binding import Binding

from .screens.dashboard import DashboardScreen
from .screens.drill_queue import DrillQueueScreen


class StudyApp(App):
    """Main TUI application presenting the unified dashboard.

    The dashboard provides an overview of study status including today's
    domain, sprint progress, reviewer status, and the drill queue. From
    here users can drill cards, browse solutions, or open the reader.
    """
    CSS_PATH = "styles/app.tcss"
    TITLE = "Study Companion"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())


class DrillApp(App):
    """Minimal app that opens directly to the drill queue screen.

    Used by `knos drill` to skip the dashboard and start drilling immediately.
    """
    CSS_PATH = "styles/app.tcss"
    TITLE = "Drill Queue"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DrillQueueScreen())


class ReaderApp(App):
    """Minimal app that opens directly to the reader material selection.

    Used by `knos read` to skip the dashboard and start reading immediately.
    """
    CSS_PATH = "styles/app.tcss"
    TITLE = "Reader"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        from knos.reader.screens import SelectMaterialScreen
        self.push_screen(SelectMaterialScreen())


if __name__ == "__main__":
    app = StudyApp()
    app.run()
