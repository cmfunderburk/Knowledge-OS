from pathlib import Path
from textual.screen import Screen
from textual.widgets import Input, ListView, ListItem, Label, Header, Footer
from textual.containers import Container
from textual.binding import Binding

from knos.reviewer.core import collect_all_solutions, load_schedule, get_solution_key
from .drill import DrillScreen

class BrowseScreen(Screen):
    """Screen for browsing all solutions."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.item_map: dict[str, Path] = {}
        self.all_files: list[Path] = []
        self.schedule: dict = {}
        self._item_counter = 0

    def compose(self):
        yield Header()
        yield Container(
            Input(placeholder="Filter files...", id="filter"),
            ListView(id="solution-list"),
            id="browse-container"
        )
        yield Footer()

    async def on_mount(self):
        self.all_files = collect_all_solutions()
        self.schedule = load_schedule()
        await self.update_list()
        self.query_one(Input).focus()

    async def on_input_changed(self, event: Input.Changed):
        await self.update_list(event.value)

    async def update_list(self, filter_text: str = ""):
        list_view = self.query_one(ListView)

        # Remove all existing children
        for child in list(list_view.children):
            await child.remove()

        self.item_map = {}
        self._item_counter = 0

        filter_lower = filter_text.lower()

        for path in self.all_files:
            key = get_solution_key(path)
            if filter_lower and filter_lower not in key.lower():
                continue

            entry = self.schedule.get(key, {})
            box = entry.get("box", "New")

            label = f"{key}   --   Box {box}"
            # Use incrementing counter for unique IDs across filter changes
            item_id = f"browse-item-{self._item_counter}"
            self._item_counter += 1
            self.item_map[item_id] = path

            await list_view.mount(ListItem(Label(label), id=item_id))

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item and event.item.id:
            path = self.item_map.get(event.item.id)
            if path:
                self.app.push_screen(DrillScreen(path))