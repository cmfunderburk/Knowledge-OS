"""Session browser screen for reviewing past dialogues and generating cards."""
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView, Static
from textual.containers import Container
from textual.binding import Binding

from knos.reader.config import load_registry
from knos.reader.content import ContentId, format_content_id
from knos.reader.session import list_sessions, Session, SESSIONS_DIR


class SessionItem(ListItem):
    """A session item showing material/chapter with metadata."""

    def __init__(
        self,
        material_id: str,
        material_title: str,
        content_id: ContentId,
        session: Session,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_title = material_title
        self.content_id = content_id
        self.session = session

    def compose(self) -> ComposeResult:
        # Format metadata
        exchanges = self.session.exchange_count
        modes = self.session.mode_distribution
        mode_str = ", ".join(f"{m}:{c}" for m, c in modes.items()) if modes else "none"

        content_label = format_content_id(self.content_id)
        yield Label(
            f"[bold]{self.material_title}[/bold] · {content_label}: {self.session.chapter_title}"
        )
        yield Label(
            f"  [dim]{exchanges} exchanges · modes: {mode_str}[/dim]",
            classes="session-meta",
        )


class SessionBrowserScreen(Screen):
    """Screen for browsing saved sessions and generating cards."""

    BINDINGS = [
        Binding("enter", "generate", "Generate Cards"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="sessions-container"):
            yield Label("[bold]Saved Sessions[/bold]", id="sessions-header")
            yield Label(
                "[dim]Select a session and press Enter to generate card drafts[/dim]",
                id="sessions-hint",
            )
            yield ListView(id="sessions-list")

        yield Footer()

    def on_mount(self) -> None:
        self.load_sessions()

    def load_sessions(self) -> None:
        """Load all sessions across all materials."""
        list_view = self.query_one("#sessions-list", ListView)
        list_view.clear()

        # Check if sessions directory exists
        if not SESSIONS_DIR.exists():
            list_view.append(ListItem(Label("[dim]No sessions yet[/dim]")))
            return

        # Get registry for material titles
        registry = load_registry()
        materials = registry.get("materials", {})

        session_count = 0

        # Iterate through session directories
        for material_dir in sorted(SESSIONS_DIR.iterdir()):
            if not material_dir.is_dir():
                continue

            material_id = material_dir.name
            material_info = materials.get(material_id, {})
            material_title = material_info.get("title", material_id)

            # Get sessions for this material
            sessions = list_sessions(material_id)

            # Sort: chapters (int) first, then appendices (str)
            def sort_key(cid: ContentId) -> tuple[int, int | str]:
                if isinstance(cid, int):
                    return (0, cid)
                return (1, cid)

            for content_id in sorted(sessions.keys(), key=sort_key):
                session = sessions[content_id]
                list_view.append(
                    SessionItem(material_id, material_title, content_id, session)
                )
                session_count += 1

        if session_count == 0:
            list_view.append(ListItem(Label("[dim]No sessions yet[/dim]")))

    def action_generate(self) -> None:
        """Generate cards for the selected session."""
        list_view = self.query_one("#sessions-list", ListView)

        if not list_view.highlighted_child or not isinstance(
            list_view.highlighted_child, SessionItem
        ):
            self.notify("No session selected", severity="warning")
            return

        item = list_view.highlighted_child

        # Push to generation screen
        from .generate_cards import GenerateCardsScreen

        self.app.push_screen(
            GenerateCardsScreen(
                material_id=item.material_id,
                material_title=item.material_title,
                content_id=item.content_id,
                session=item.session,
            )
        )

    def action_back(self) -> None:
        """Go back to material selection."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_generate()
