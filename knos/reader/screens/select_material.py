"""Material selection screen for the reader."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListItem, ListView, Label
from textual.containers import Container, Vertical
from textual.binding import Binding

from knos.reader.config import load_registry, get_material_type
from knos.reader.content import list_all_content, get_source_path


class MaterialItem(ListItem):
    """A material item in the list."""

    def __init__(self, material_id: str, info: dict) -> None:
        super().__init__()
        self.material_id = material_id
        self.info = info

    def compose(self) -> ComposeResult:
        title = self.info.get("title", self.material_id)
        author = self.info.get("author", "Unknown")

        # Check if source file exists
        source_exists = get_source_path(self.material_id).exists()

        # Format based on material type
        material_type = get_material_type(self.material_id)
        if material_type == "article":
            type_label = "article"
            status = "ready" if source_exists else "missing"
        else:
            chapters, _ = list_all_content(self.material_id)
            chapter_count = len(chapters)
            type_label = f"{chapter_count} chapters"
            status = "ready" if source_exists and chapter_count > 0 else "missing"

        yield Label(f"[bold]{title}[/bold]")
        yield Label(f"  {author} · {type_label} · {status}", classes="material-meta")


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

            # Check if source exists
            source_path = get_source_path(material_id)
            if not source_path.exists():
                self.notify(f"Source not found: {source_path}", title="Missing source")
                return

            material_type = get_material_type(material_id)

            if material_type == "article":
                # Articles skip chapter selection, go directly to dialogue
                from .dialogue import DialogueScreen
                self.app.push_screen(DialogueScreen(
                    material_id=material_id,
                    material_info=info,
                    chapter_num=None,  # Signals article mode
                    chapter_title=info.get("title", material_id),
                ))
            else:
                # Books go to chapter selection
                chapters, _ = list_all_content(material_id)
                if not chapters:
                    self.notify("No chapters found in source", title="Empty source")
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
