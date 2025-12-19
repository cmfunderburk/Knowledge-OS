"""Chapter selection screen for the reader."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView
from textual.containers import Container
from textual.binding import Binding

from reader.session import list_sessions, Session


class ChapterItem(ListItem):
    """A chapter item in the list."""

    def __init__(self, chapter_num: int, title: str, session: Session | None = None) -> None:
        super().__init__()
        self.chapter_num = chapter_num
        self.chapter_title = title
        self.session = session

    def compose(self) -> ComposeResult:
        # Build status indicator
        if self.session:
            exchanges = self.session.exchange_count
            if exchanges >= 10:
                indicator = "[green]●[/green]"  # Substantial progress
            elif exchanges >= 3:
                indicator = "[yellow]◐[/yellow]"  # Some progress
            else:
                indicator = "[dim]○[/dim]"  # Just started
            status = f" {indicator} [dim]({exchanges} exchanges)[/dim]"
        else:
            status = ""

        yield Label(f"Chapter {self.chapter_num}: {self.chapter_title}{status}")


class SelectChapterScreen(Screen):
    """Screen for selecting a chapter to read."""

    BINDINGS = [
        Binding("enter", "select", "Select"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, material_id: str, material_info: dict) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_info = material_info

    def compose(self) -> ComposeResult:
        yield Header()

        title = self.material_info.get("title", self.material_id)

        with Container(id="chapter-container"):
            yield Label(f"[bold]{title}[/bold]", id="chapter-header")
            yield Label("Select a chapter:", id="chapter-subheader")
            yield ListView(id="chapter-list")

        yield Footer()

    def on_mount(self) -> None:
        self.load_chapters()

    def load_chapters(self) -> None:
        """Load chapters into the list."""
        list_view = self.query_one("#chapter-list", ListView)
        list_view.clear()

        chapters = self.material_info.get("structure", {}).get("chapters", [])

        # Get existing sessions for this material
        sessions = list_sessions(self.material_id)

        for chapter in chapters:
            num = chapter["num"]
            title = chapter["title"]
            session = sessions.get(num)
            list_view.append(ChapterItem(num, title, session))

    def action_select(self) -> None:
        """Select the highlighted chapter."""
        list_view = self.query_one("#chapter-list", ListView)
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, ChapterItem):
            chapter_num = list_view.highlighted_child.chapter_num
            chapter_title = list_view.highlighted_child.chapter_title

            from .dialogue import DialogueScreen
            self.app.push_screen(DialogueScreen(
                material_id=self.material_id,
                material_info=self.material_info,
                chapter_num=chapter_num,
                chapter_title=chapter_title,
            ))

    def action_back(self) -> None:
        """Go back to material selection."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_select()
