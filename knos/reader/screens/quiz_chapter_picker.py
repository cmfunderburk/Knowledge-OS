"""Chapter picker specifically for quiz mode."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ListItem, ListView
from textual.containers import Container
from textual.binding import Binding

from knos.reader.content import ContentId, list_all_content
from knos.reader.session import list_quiz_sessions


class QuizChapterItem(ListItem):
    """Chapter item showing quiz history count."""

    def __init__(
        self,
        content_id: ContentId,
        title: str,
        quiz_count: int,
    ) -> None:
        super().__init__()
        self.content_id = content_id
        self.content_title = title
        self.quiz_count = quiz_count

    def compose(self) -> ComposeResult:
        if isinstance(self.content_id, int):
            label = f"Chapter {self.content_id}: {self.content_title}"
        else:
            label = f"Appendix {self.content_id}: {self.content_title}"

        if self.quiz_count > 0:
            indicator = f" [dim]({self.quiz_count} prior quizzes)[/dim]"
        else:
            indicator = ""

        yield Label(f"{label}{indicator}")


class SectionLabel(ListItem):
    """A non-selectable section label."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.disabled = True

    def compose(self) -> ComposeResult:
        yield Label(f"[bold dim]{self.text}[/bold dim]")


class QuizChapterPickerScreen(Screen):
    """Screen for selecting a chapter to quiz on."""

    BINDINGS = [
        Binding("enter", "select", "Start Quiz"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self, material_id: str, material_info: dict) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_info = material_info

    def compose(self) -> ComposeResult:
        title = self.material_info.get("title", self.material_id)

        yield Header()
        with Container(id="quiz-picker-container"):
            yield Label(f"[bold]Quiz: {title}[/bold]", id="quiz-header")
            yield Label("[dim]Select a chapter to quiz on. Each quiz is a fresh session.[/dim]", id="quiz-subheader")
            yield ListView(id="quiz-chapter-list")
        yield Footer()

    def on_mount(self) -> None:
        self.load_chapters()

    def load_chapters(self) -> None:
        """Load chapters and appendices with quiz counts."""
        list_view = self.query_one("#quiz-chapter-list", ListView)
        list_view.clear()

        chapters, appendices = list_all_content(self.material_id)
        quiz_sessions = list_quiz_sessions(self.material_id)

        # Add chapters
        if chapters:
            list_view.append(SectionLabel("─── Chapters ───"))
            for chapter in chapters:
                num = chapter["num"]
                title = chapter["title"]
                prefix = f"ch{num:02d}"
                quiz_count = len(quiz_sessions.get(prefix, []))
                list_view.append(QuizChapterItem(num, title, quiz_count))

        # Add appendices
        if appendices:
            list_view.append(SectionLabel("─── Appendices ───"))
            for appendix in appendices:
                app_id = appendix["id"]
                title = appendix["title"]
                prefix = f"app{app_id}"
                quiz_count = len(quiz_sessions.get(prefix, []))
                list_view.append(QuizChapterItem(app_id, title, quiz_count))

    def action_select(self) -> None:
        """Start a quiz on the selected chapter."""
        list_view = self.query_one("#quiz-chapter-list", ListView)
        item = list_view.highlighted_child

        if item and isinstance(item, QuizChapterItem):
            from .dialogue import DialogueScreen
            self.app.push_screen(DialogueScreen(
                material_id=self.material_id,
                material_info=self.material_info,
                chapter_num=item.content_id,
                chapter_title=item.content_title,
                mode_override="quiz",
                is_quiz_session=True,
            ))

    def action_back(self) -> None:
        """Go back to chapter selection."""
        self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection via click."""
        self.action_select()
