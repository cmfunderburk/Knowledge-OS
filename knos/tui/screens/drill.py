"""
Drill screen: line-by-line code recall practice.

Parses a solution markdown file and presents each fenced code block as a
RevealBlock widget. The user marks each line as known (y) or unknown (n),
building a score. Perfect scores advance the card's Leitner box; any
failure resets to box 0.
"""
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Markdown, Static, Label
from textual.containers import VerticalScroll, Container
from textual.binding import Binding

from knos.reviewer.core import parse_markdown, SessionResult, update_schedule, append_history
from knos.tui.widgets.reveal_block import RevealBlock


class DrillScreen(Screen):
    """Interactive drill session for a single solution card.

    Displays the card's prose interleaved with RevealBlock widgets for each
    code block. Users press y/n to mark lines correct/incorrect, or s to
    skip remaining lines in the current block.

    On session completion, updates schedule.json (advancing or resetting
    the Leitner box) and appends results to history.jsonl. If more cards
    remain in the queue, pressing Enter advances to the next card.
    """

    BINDINGS = [
        Binding("y", "answer_yes", "Knew it"),
        Binding("n", "answer_no", "Didn't know"),
        Binding("s", "skip_block", "Skip Block"),
        Binding("enter", "next_drill", "Next", show=False),
        Binding("q", "quit_drill", "Quit"),
    ]

    def __init__(self, solution_path: Path, drill_queue: list[tuple[Path, dict]] | None = None):
        super().__init__()
        self.solution_path = solution_path
        self.drill_queue = drill_queue or []
        self.parsed = parse_markdown(solution_path.read_text())
        self.blocks = self.parsed.target_blocks
        self.reveal_widgets: list[RevealBlock] = []
        self.current_block_idx = 0
        self.session_complete = False
        self._next_path: Path | None = None  # Set after session completes

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(f"Drilling: {self.solution_path.name}", classes="header"),
            id="drill-header"
        )
        
        with VerticalScroll(id="drill-scroll"):
            # Interleave prose and blocks
            last_pos = 0
            raw = self.parsed.raw_text
            
            for i, block in enumerate(self.blocks):
                # Prose before
                if block.start_pos > last_pos:
                    prose = raw[last_pos:block.start_pos]
                    if prose.strip():
                        yield Markdown(prose)
                
                # The Block
                rw = RevealBlock(block, i + 1, len(self.blocks), id=f"block-{i}")
                self.reveal_widgets.append(rw)
                yield rw
                
                last_pos = block.end_pos
            
            # Trailing prose
            if last_pos < len(raw):
                prose = raw[last_pos:]
                if prose.strip():
                    yield Markdown(prose)
                    
            # Padding at bottom for scrolling
            yield Static("\n" * 5)
            
        yield Footer()

    def on_mount(self) -> None:
        # Focus the scroll container so keys work? 
        # Actually Screen handles keys via bindings.
        # Ensure we scroll to start.
        pass

    def action_answer_yes(self):
        self._handle_answer(True)

    def action_answer_no(self):
        self._handle_answer(False)

    def action_skip_block(self):
        if self.session_complete:
            return
        
        widget = self.reveal_widgets[self.current_block_idx]
        widget.skip_remaining()
        self._check_advance()

    def _handle_answer(self, success: bool):
        if self.session_complete:
            return

        widget = self.reveal_widgets[self.current_block_idx]
        if not widget.complete:
            widget.reveal_line(success)
            
        self._check_advance()

    def _check_advance(self):
        """Check if current block is done, advance if so."""
        widget = self.reveal_widgets[self.current_block_idx]
        
        if widget.complete:
            # Move to next block
            if self.current_block_idx < len(self.blocks) - 1:
                self.current_block_idx += 1
                next_widget = self.reveal_widgets[self.current_block_idx]
                next_widget.scroll_visible()
            else:
                self._finish_session()

    def _finish_session(self):
        """Calculate score and show summary."""
        if self.session_complete:
            return

        self.session_complete = True

        # Calculate results
        results = [w.get_result() for w in self.reveal_widgets]

        total_lines = sum(len(r.lines) for r in results)
        correct_lines = sum(sum(r.results) for r in results)
        score = 100.0 * correct_lines / total_lines if total_lines > 0 else 100.0

        session_result = SessionResult(
            blocks=results,
            total_lines=total_lines,
            correct_lines=correct_lines,
            score=score,
            solution_path=self.solution_path
        )

        # Save data
        update_schedule(self.solution_path, score)
        append_history(session_result)

        # Find next card in queue (skip current one)
        self._next_path = None
        for path, _meta in self.drill_queue:
            if path != self.solution_path:
                self._next_path = path
                break

        # Build completion message
        msg = f"Score: {score:.1f}%"
        if score >= 100:
            msg += " - PERFECT! Next box."
        else:
            msg += " - Reset to Box 0."

        if self._next_path:
            msg += f"\n\nEnter: next card  |  q: quit"
        else:
            msg += f"\n\nq: quit (no more cards)"

        self.notify(msg, timeout=10)
        self.app.bell()

    def action_next_drill(self):
        """Advance to the next card in the queue (only works after session complete)."""
        if not self.session_complete:
            return
        if self._next_path:
            # Clear lingering notifications before advancing
            self.app.clear_notifications()
            # Dismiss with the next path as result; dashboard will handle it
            self.dismiss({"next_path": self._next_path, "queue": self.drill_queue})
        else:
            self.notify("No more cards in queue", timeout=2)

    def action_quit_drill(self):
        self.dismiss()
