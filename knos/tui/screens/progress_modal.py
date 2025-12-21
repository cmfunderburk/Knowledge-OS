"""
Progress report modal for viewing the progress dashboard in-TUI.
"""
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Markdown, Footer, Static
from textual.containers import Container, VerticalScroll
from textual.binding import Binding

from knos.reviewer.core import generate_progress_report, REPO_ROOT


class ProgressModal(ModalScreen):
    """Modal screen displaying the progress report."""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("e", "export", "Export"),
    ]
    
    DEFAULT_CSS = """
    ProgressModal {
        align: center middle;
    }
    
    #progress-container {
        width: 90%;
        height: 90%;
        border: solid $primary;
        background: $surface;
    }
    
    #progress-scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    
    #progress-footer {
        dock: bottom;
        width: 100%;
        height: 1;
        background: $primary-background;
        color: $text-muted;
        text-align: center;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.report_content = generate_progress_report()
    
    def compose(self) -> ComposeResult:
        with Container(id="progress-container"):
            with VerticalScroll(id="progress-scroll"):
                yield Markdown(self.report_content, id="progress-md")
            yield Static("ESC/q: Close │ e: Export to PROGRESS.md", id="progress-footer")
    
    def action_close(self) -> None:
        """Close the modal."""
        self.dismiss()
    
    def action_export(self) -> None:
        """Export the report to PROGRESS.md."""
        output_path = REPO_ROOT / "PROGRESS.md"
        output_path.write_text(self.report_content)
        self.notify("Exported to PROGRESS.md", timeout=2)


class SyllabusModal(ModalScreen):
    """Modal screen displaying the syllabus or priority shift file."""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]
    
    DEFAULT_CSS = """
    SyllabusModal {
        align: center middle;
    }
    
    #syllabus-container {
        width: 90%;
        height: 90%;
        border: solid $primary;
        background: $surface;
    }
    
    #syllabus-scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    
    #syllabus-footer {
        dock: bottom;
        width: 100%;
        height: 1;
        background: $primary-background;
        color: $text-muted;
        text-align: center;
    }
    """
    
    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        if file_path.exists():
            self.content = file_path.read_text()
        else:
            self.content = f"# Error\n\nFile not found: {file_path}"
    
    def compose(self) -> ComposeResult:
        with Container(id="syllabus-container"):
            with VerticalScroll(id="syllabus-scroll"):
                yield Markdown(self.content)
            yield Static(f"Viewing: {self.file_path.name} │ ESC/q: Close", id="syllabus-footer")
    
    def action_close(self) -> None:
        self.dismiss()
