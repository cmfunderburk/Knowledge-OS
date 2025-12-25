"""Browser for viewing past quiz sessions."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView, RichLog
from textual.containers import Container
from textual.binding import Binding
from rich.markdown import Markdown

from knos.reader.content import ContentId
from knos.reader.session import (
    list_quiz_sessions,
    load_transcript_by_prefix,
    Session,
)


class QuizSessionItem(ListItem):
    """A quiz session showing date and performance."""

    def __init__(
        self,
        material_id: str,
        content_id: ContentId,
        session: Session,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.content_id = content_id
        self.session = session

    def compose(self) -> ComposeResult:
        # Format content label
        if isinstance(self.content_id, int):
            content_label = f"Chapter {self.content_id}"
        elif self.content_id:
            content_label = f"Appendix {self.content_id}"
        else:
            content_label = "Article"

        # Format date and exchange count
        date_str = self.session.started.strftime("%Y-%m-%d %H:%M")
        exchanges = self.session.exchange_count

        yield Label(f"[bold]{content_label}[/bold]: {self.session.chapter_title}")
        yield Label(f"  [dim]{date_str} · {exchanges} questions[/dim]")


class SectionLabel(ListItem):
    """A non-selectable section label."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.disabled = True

    def compose(self) -> ComposeResult:
        yield Label(f"[bold dim]{self.text}[/bold dim]")


class QuizHistoryScreen(Screen):
    """Screen for browsing quiz session history."""

    BINDINGS = [
        Binding("enter", "view", "View"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self, material_id: str, material_info: dict) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_info = material_info
        self._viewing_transcript = False

    def compose(self) -> ComposeResult:
        title = self.material_info.get("title", self.material_id)

        yield Header()
        with Container(id="quiz-history-container"):
            yield Label(f"[bold]Quiz History: {title}[/bold]", id="quiz-history-header")
            yield ListView(id="quiz-history-list")
            yield RichLog(id="quiz-transcript", wrap=True, highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        # Hide transcript view initially
        transcript_log = self.query_one("#quiz-transcript", RichLog)
        transcript_log.display = False
        self.load_quiz_sessions()

    def load_quiz_sessions(self) -> None:
        """Load all quiz sessions for this material."""
        list_view = self.query_one("#quiz-history-list", ListView)
        list_view.clear()

        quiz_sessions = list_quiz_sessions(self.material_id)

        if not quiz_sessions:
            list_view.append(SectionLabel("No quiz sessions yet"))
            return

        # Flatten and sort by date (newest first)
        all_sessions: list[tuple[str, Session]] = []
        for prefix, sessions in quiz_sessions.items():
            for session in sessions:
                all_sessions.append((prefix, session))

        all_sessions.sort(key=lambda x: x[1].started, reverse=True)

        list_view.append(SectionLabel(f"─── {len(all_sessions)} Quiz Sessions ───"))

        for _, session in all_sessions:
            list_view.append(QuizSessionItem(
                self.material_id,
                session.chapter_num,
                session,
            ))

    def action_view(self) -> None:
        """View the transcript of the selected quiz session."""
        if self._viewing_transcript:
            # Toggle back to list view
            self._hide_transcript()
            return

        list_view = self.query_one("#quiz-history-list", ListView)
        item = list_view.highlighted_child

        if item and isinstance(item, QuizSessionItem):
            self._show_transcript(item.session)

    def _show_transcript(self, session: Session) -> None:
        """Display the transcript of a quiz session."""
        if not session.session_prefix:
            self.notify("No transcript available", severity="warning")
            return

        transcript = load_transcript_by_prefix(self.material_id, session.session_prefix)
        if not transcript:
            self.notify("No transcript available", severity="warning")
            return

        # Hide list, show transcript
        list_view = self.query_one("#quiz-history-list", ListView)
        transcript_log = self.query_one("#quiz-transcript", RichLog)

        list_view.display = False
        transcript_log.display = True
        transcript_log.clear()
        self._viewing_transcript = True

        # Display header
        date_str = session.started.strftime("%Y-%m-%d %H:%M")
        if isinstance(session.chapter_num, int):
            content_label = f"Chapter {session.chapter_num}"
        elif session.chapter_num:
            content_label = f"Appendix {session.chapter_num}"
        else:
            content_label = "Article"

        transcript_log.write(f"[bold]{content_label}: {session.chapter_title}[/bold]")
        transcript_log.write(f"[dim]{date_str} · {session.exchange_count} exchanges[/dim]")
        transcript_log.write("[dim]Press Enter to return to list[/dim]")
        transcript_log.write("")
        transcript_log.write("[dim]─── Transcript ───[/dim]")
        transcript_log.write("")

        # Display messages
        for msg in transcript:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                transcript_log.write("[bold yellow]You[/bold yellow]")
                transcript_log.write(f"  {content}")
            else:
                transcript_log.write("[bold blue]Reader[/bold blue] [blue][quiz][/blue]")
                transcript_log.write(Markdown(content.strip()))

            transcript_log.write("")

    def _hide_transcript(self) -> None:
        """Hide transcript and show list again."""
        list_view = self.query_one("#quiz-history-list", ListView)
        transcript_log = self.query_one("#quiz-transcript", RichLog)

        transcript_log.display = False
        transcript_log.clear()
        list_view.display = True
        self._viewing_transcript = False

    def action_back(self) -> None:
        """Go back to chapter selection."""
        if self._viewing_transcript:
            self._hide_transcript()
        else:
            self.app.pop_screen()
