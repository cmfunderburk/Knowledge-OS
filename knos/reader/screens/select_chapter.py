"""Chapter selection screen for the reader."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView
from textual.containers import Container
from textual.binding import Binding

from knos.reader.content import ContentId, list_all_content
from knos.reader.session import (
    list_sessions,
    list_quiz_sessions,
    load_all_transcripts,
    Session,
)


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


class SpecialMenuItem(ListItem):
    """A special action item (Review, Quiz, etc.) in the chapter list."""

    def __init__(
        self,
        action: str,
        title: str,
        description: str,
        indicator: str = "",
    ) -> None:
        super().__init__()
        self.action = action  # "review", "quiz", "quiz_history"
        self.menu_title = title
        self.description = description
        self.indicator = indicator  # e.g., session count indicator

    def compose(self) -> ComposeResult:
        yield Label(f"[bold cyan]{self.menu_title}[/bold cyan]{self.indicator}")
        yield Label(f"  [dim]{self.description}[/dim]")


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
        quiz_sessions = list_quiz_sessions(self.material_id)

        # Add Study Tools section
        list_view.append(SectionLabel("─── Study Tools ───"))

        # Review option (only show if there are regular sessions)
        if sessions:
            session_count = len(sessions)
            indicator = f" [dim]({session_count} sessions)[/dim]"
            list_view.append(SpecialMenuItem(
                action="review",
                title="Review All Discussions",
                description="Synthesize across all chapter discussions",
                indicator=indicator,
            ))

        # Quiz option (always show if there are chapters)
        if chapters or appendices:
            list_view.append(SpecialMenuItem(
                action="quiz",
                title="Quiz Mode",
                description="Test your recall on a specific chapter",
            ))

        # Quiz history (only show if there are quiz sessions)
        if quiz_sessions:
            total_quizzes = sum(len(s) for s in quiz_sessions.values())
            indicator = f" [dim]({total_quizzes} quizzes)[/dim]"
            list_view.append(SpecialMenuItem(
                action="quiz_history",
                title="Browse Quiz History",
                description="View past quiz sessions",
                indicator=indicator,
            ))

        # Add chapters section
        if chapters:
            list_view.append(SectionLabel("─── Chapters ───"))
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
        """Select the highlighted content or special action."""
        list_view = self.query_one("#chapter-list", ListView)
        item = list_view.highlighted_child

        if item and isinstance(item, SpecialMenuItem):
            if item.action == "review":
                self._open_review_dialogue()
            elif item.action == "quiz":
                self._open_quiz_picker()
            elif item.action == "quiz_history":
                self._open_quiz_history()
        elif item and isinstance(item, ContentItem):
            content_id = item.content_id
            content_title = item.content_title

            from .dialogue import DialogueScreen
            self.app.push_screen(DialogueScreen(
                material_id=self.material_id,
                material_info=self.material_info,
                chapter_num=content_id,
                chapter_title=content_title,
            ))

    def _open_review_dialogue(self) -> None:
        """Open the review dialogue with all transcripts as context."""
        # Load all transcripts for this material
        transcripts = load_all_transcripts(self.material_id)

        if not transcripts:
            self.notify("No discussions to review yet.", severity="warning")
            return

        from .dialogue import DialogueScreen
        material_title = self.material_info.get("title", self.material_id)
        self.app.push_screen(DialogueScreen(
            material_id=self.material_id,
            material_info=self.material_info,
            chapter_num=None,
            chapter_title=f"Review: {material_title}",
            mode_override="review",
            context_override=transcripts,
        ))

    def _open_quiz_picker(self) -> None:
        """Open the quiz chapter picker screen."""
        from .quiz_chapter_picker import QuizChapterPickerScreen
        self.app.push_screen(QuizChapterPickerScreen(
            material_id=self.material_id,
            material_info=self.material_info,
        ))

    def _open_quiz_history(self) -> None:
        """Open the quiz history browser."""
        from .quiz_history import QuizHistoryScreen
        self.app.push_screen(QuizHistoryScreen(
            material_id=self.material_id,
            material_info=self.material_info,
        ))

    def action_back(self) -> None:
        """Go back to material selection."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_select()
