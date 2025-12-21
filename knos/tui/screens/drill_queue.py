from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from knos.reviewer.core import get_drill_queue
from knos.tui.widgets.panels import DrillListPanel
from .drill import DrillScreen


class DrillQueueScreen(Screen):
    """Minimal drill launcher showing the due queue."""

    BINDINGS = [
        Binding("enter", "drill_selected", "Drill Selected"),
        Binding("d", "drill_all", "Drill All"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("r", "refresh_queue", "Refresh"),
        Binding("q", "app.quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.drill_queue: list[tuple] = []
        self.selected_idx = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="drill-queue"):
            yield Static(
                "Due cards: failed → overdue → due → new.  Enter: drill selection, d: drill all, r: refresh, q: quit.",
                id="drill-hint",
            )
            yield DrillListPanel(self.drill_queue, self.selected_idx, id="drill-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_queue()

    async def refresh_queue(self) -> None:
        self.drill_queue = get_drill_queue()
        self.selected_idx = 0

        drill_list = self.query_one("#drill-list", DrillListPanel)
        drill_list.drill_queue = self.drill_queue
        drill_list.selected_idx = self.selected_idx
        drill_list.refresh()

        if not self.drill_queue:
            self.notify("No cards due!", timeout=3)

    def action_move_up(self) -> None:
        if self.drill_queue:
            self.selected_idx = max(0, self.selected_idx - 1)
            self.query_one("#drill-list", DrillListPanel).update_selection(self.selected_idx)

    def action_move_down(self) -> None:
        if self.drill_queue:
            self.selected_idx = min(len(self.drill_queue) - 1, self.selected_idx + 1)
            self.query_one("#drill-list", DrillListPanel).update_selection(self.selected_idx)

    def _start_drill(self, queue: list[tuple]) -> None:
        if not queue:
            self.notify("Nothing to drill!", timeout=3)
            return

        path = queue[0][0]
        self.app.push_screen(
            DrillScreen(path, drill_queue=queue),
            callback=self.on_drill_finished,
        )

    def action_drill_selected(self) -> None:
        if not self.drill_queue:
            self.notify("Nothing to drill!", timeout=3)
            return
        queue_from_selected = self.drill_queue[self.selected_idx:]
        self._start_drill(queue_from_selected)

    def action_drill_all(self) -> None:
        self._start_drill(self.drill_queue)

    def action_refresh_queue(self) -> None:
        self.app.call_later(self.refresh_queue)
        self.notify("Refreshed", timeout=1)

    async def on_drill_finished(self, result=None) -> None:
        """Advance through the queue or refresh when done."""
        if result and isinstance(result, dict) and "next_path" in result:
            next_path = result["next_path"]
            old_queue = result.get("queue", [])

            remaining_queue = old_queue
            for i, (path, _meta) in enumerate(old_queue):
                if path == next_path:
                    remaining_queue = old_queue[i:]
                    break

            self.app.push_screen(
                DrillScreen(next_path, drill_queue=remaining_queue),
                callback=self.on_drill_finished,
            )
        else:
            await self.refresh_queue()
