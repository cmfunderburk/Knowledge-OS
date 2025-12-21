"""Chapter selection screen for the reader."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView
from textual.containers import Container
from textual.binding import Binding

from reader.content import ContentId, list_all_content
from reader.session import list_sessions, Session


class ContentItem(ListItem):
    """A content item (chapter or appendix) in the list."""

    def __init__(
        self,
        content_id: ContentId,
        title: str,
        session: Session | None = None,
    ) -> None:
        super().__init__()
        self.content_id = content_id
        self.content_title = title
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

        # Format label based on content type
        if isinstance(self.content_id, int):
            label = f"Chapter {self.content_id}: {self.content_title}"
        else:
            label = f"Appendix {self.content_id}: {self.content_title}"

        yield Label(f"{label}{status}")


class SectionLabel(ListItem):
    """A non-selectable section label."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.disabled = True

    def compose(self) -> ComposeResult:
        yield Label(f"[bold dim]{self.text}[/bold dim]")


class SelectChapterScreen(Screen):
    """Screen for selecting a chapter or appendix to read."""

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
            yield Label("Select a chapter or appendix:", id="chapter-subheader")
            yield ListView(id="chapter-list")

        yield Footer()

    def on_mount(self) -> None:
        self.load_content()

    def load_content(self) -> None:
        """Load chapters and appendices into the list."""
        list_view = self.query_one("#chapter-list", ListView)
        list_view.clear()

        chapters, appendices = list_all_content(self.material_id)

        # Get existing sessions for this material
        sessions = list_sessions(self.material_id)

        # Add chapters
        for chapter in chapters:
            num = chapter["num"]
            title = chapter["title"]
            session = sessions.get(num)
            list_view.append(ContentItem(num, title, session))

        # Add appendices section if any exist
        if appendices:
            list_view.append(SectionLabel("─── Appendices ───"))
            for appendix in appendices:
                app_id = appendix["id"]
                title = appendix["title"]
                session = sessions.get(app_id)
                list_view.append(ContentItem(app_id, title, session))

    def action_select(self) -> None:
        """Select the highlighted content."""
        list_view = self.query_one("#chapter-list", ListView)
        item = list_view.highlighted_child

        if item and isinstance(item, ContentItem):
            content_id = item.content_id
            content_title = item.content_title

            from .dialogue import DialogueScreen
            self.app.push_screen(DialogueScreen(
                material_id=self.material_id,
                material_info=self.material_info,
                chapter_num=content_id,
                chapter_title=content_title,
            ))

    def action_back(self) -> None:
        """Go back to material selection."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_select()
