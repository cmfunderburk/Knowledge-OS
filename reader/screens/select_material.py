"""Material selection screen for the reader."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListItem, ListView, Label
from textual.containers import Container, Vertical
from textual.binding import Binding

from reader.config import load_registry
from reader.content import list_extracted_chapters


class MaterialItem(ListItem):
    """A material item in the list."""

    def __init__(self, material_id: str, info: dict) -> None:
        super().__init__()
        self.material_id = material_id
        self.info = info

    def compose(self) -> ComposeResult:
        title = self.info.get("title", self.material_id)
        author = self.info.get("author", "Unknown")
        chapters = len(self.info.get("structure", {}).get("chapters", []))
        extracted = len(list_extracted_chapters(self.material_id))

        status = "ready" if extracted == chapters else f"{extracted}/{chapters} extracted"

        yield Label(f"[bold]{title}[/bold]")
        yield Label(f"  {author} · {chapters} chapters · {status}", classes="material-meta")


class SelectMaterialScreen(Screen):
    """Screen for selecting a material to read."""

    BINDINGS = [
        Binding("enter", "select", "Select"),
        Binding("s", "sessions", "Sessions"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="material-container"):
            yield Label("[bold]Select Material[/bold]", id="material-header")
            yield ListView(id="material-list")

        yield Footer()

    def on_mount(self) -> None:
        self.load_materials()

    def load_materials(self) -> None:
        """Load materials from registry into the list."""
        registry = load_registry()
        materials = registry.get("materials", {})

        list_view = self.query_one("#material-list", ListView)
        list_view.clear()

        if not materials:
            list_view.append(ListItem(Label("No materials registered.")))
            return

        for material_id, info in materials.items():
            list_view.append(MaterialItem(material_id, info))

    def action_select(self) -> None:
        """Select the highlighted material."""
        list_view = self.query_one("#material-list", ListView)
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, MaterialItem):
            material_id = list_view.highlighted_child.material_id
            info = list_view.highlighted_child.info

            # Check if extracted
            chapters = len(info.get("structure", {}).get("chapters", []))
            extracted = len(list_extracted_chapters(material_id))

            if extracted < chapters:
                self.notify(f"Run: ./read --extract {material_id}", title="Not extracted")
                return

            from .select_chapter import SelectChapterScreen
            self.app.push_screen(SelectChapterScreen(material_id, info))

    def action_sessions(self) -> None:
        """Open sessions browser."""
        from .sessions import SessionBrowserScreen

        self.app.push_screen(SessionBrowserScreen())

    def action_back(self) -> None:
        """Go back (quit for root screen)."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_select()
