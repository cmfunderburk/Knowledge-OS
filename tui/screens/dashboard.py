from datetime import datetime
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from reviewer.core import get_drill_queue, generate_progress_report, REPO_ROOT, PLAN_DIR, get_priority_shift_config
from tui.widgets.panels import TodayPanel, ProgressPanel, StatusPanel, DrillListPanel
from .drill import DrillScreen
from .browse import BrowseScreen
from .progress_modal import ProgressModal, SyllabusModal


class DashboardScreen(Screen):
    """The unified command center dashboard."""
    
    BINDINGS = [
        Binding("d", "drill_all", "Drill All"),
        Binding("enter", "drill_selected", "Drill Selected"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("b", "browse", "Browse"),
        Binding("p", "progress_preview", "Progress"),
        Binding("P", "progress_export", "Export", show=False),
        Binding("s", "view_syllabus", "Syllabus"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.drill_queue = []
        self.selected_idx = 0

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="dashboard-main"):
            # Top row: Today + Progress side by side
            with Horizontal(id="top-row"):
                yield TodayPanel(id="today-panel")
                yield ProgressPanel(id="progress-panel")
            
            # Middle: Status panel (full width)
            yield StatusPanel(id="status-panel")
            
            # Bottom: Drill list
            yield DrillListPanel([], 0, id="drill-list")
        
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Reload all dashboard data."""
        self.drill_queue = get_drill_queue()
        self.selected_idx = 0
        
        # Update drill list widget
        drill_list = self.query_one("#drill-list", DrillListPanel)
        drill_list.drill_queue = self.drill_queue
        drill_list.selected_idx = self.selected_idx
        drill_list.refresh()
        
        # Refresh all panels
        self.query_one("#today-panel", TodayPanel).refresh()
        self.query_one("#progress-panel", ProgressPanel).refresh()
        self.query_one("#status-panel", StatusPanel).refresh()

    def action_move_up(self) -> None:
        if self.drill_queue:
            self.selected_idx = max(0, self.selected_idx - 1)
            drill_list = self.query_one("#drill-list", DrillListPanel)
            drill_list.update_selection(self.selected_idx)

    def action_move_down(self) -> None:
        if self.drill_queue:
            self.selected_idx = min(len(self.drill_queue) - 1, self.selected_idx + 1)
            drill_list = self.query_one("#drill-list", DrillListPanel)
            drill_list.update_selection(self.selected_idx)

    def action_drill_selected(self) -> None:
        if not self.drill_queue:
            self.notify("Nothing to drill!")
            return

        path = self.drill_queue[self.selected_idx][0]
        # Build queue starting from selected card
        queue_from_selected = self.drill_queue[self.selected_idx:]
        self.app.push_screen(
            DrillScreen(path, drill_queue=queue_from_selected),
            callback=self.on_drill_finished
        )

    def action_drill_all(self) -> None:
        if not self.drill_queue:
            self.notify("Nothing to drill!")
            return

        path = self.drill_queue[0][0]
        self.app.push_screen(
            DrillScreen(path, drill_queue=self.drill_queue),
            callback=self.on_drill_finished
        )

    def action_browse(self) -> None:
        self.app.push_screen(BrowseScreen())

    def action_progress_preview(self) -> None:
        """Show progress report in a modal."""
        self.app.push_screen(ProgressModal())

    def action_view_syllabus(self) -> None:
        """Show syllabus or priority shift milestones file."""
        priority_shift = get_priority_shift_config()

        # Check for milestones file in config
        if priority_shift.get("enabled") and priority_shift.get("milestones_file"):
            target_file = REPO_ROOT / priority_shift["milestones_file"]
            if target_file.exists():
                self.app.push_screen(SyllabusModal(target_file))
                return

        # Fall back to syllabus.md or todo.md in plan/
        syllabus = PLAN_DIR / "syllabus.md"
        todo = PLAN_DIR / "todo.md"
        target_file = syllabus if syllabus.exists() else todo
        self.app.push_screen(SyllabusModal(target_file))

    def action_progress_export(self) -> None:
        """Generate and save progress report to file."""
        report = generate_progress_report()
        output_path = REPO_ROOT / "PROGRESS.md"
        output_path.write_text(report)
        self.notify(f"Progress report saved to PROGRESS.md", timeout=3)

    def action_refresh(self) -> None:
        self.app.call_later(self.refresh_data)
        self.notify("Refreshed!", timeout=1)

    async def on_drill_finished(self, result=None) -> None:
        """Handle drill completion - either advance to next card or refresh."""
        if result and isinstance(result, dict) and "next_path" in result:
            # User pressed Enter to advance to next card
            next_path = result["next_path"]
            # Build remaining queue (exclude the card we just finished)
            old_queue = result.get("queue", [])
            remaining_queue = [(p, m) for p, m in old_queue if p != next_path]
            # Find the position of next_path in old_queue to get remaining
            for i, (p, _m) in enumerate(old_queue):
                if p == next_path:
                    remaining_queue = old_queue[i:]
                    break
            self.app.push_screen(
                DrillScreen(next_path, drill_queue=remaining_queue),
                callback=self.on_drill_finished
            )
        else:
            # Normal quit - refresh dashboard
            await self.refresh_data()
