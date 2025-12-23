"""
RevealBlock widget for line-by-line code drilling.

The core interactive component of drill sessions. Each code block from a
solution card becomes a RevealBlock that hides lines until the user marks
them correct (y) or incorrect (n). Lines are displayed with syntax
highlighting once revealed, with checkmarks or X marks indicating success.

Supports two block types:
- "code": Traditional line-by-line recall with length hints
- "slots": Prompt::Answer format where prompts are visible, answers hidden
"""
from rich.console import RenderableType
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget
from textual.reactive import reactive

from knos.reviewer.core import CodeBlock, BlockResult, parse_slot_line, SlotLine


class RevealBlock(Widget):
    """Interactive widget for line-by-line code recall.

    Displays a code block with lines initially hidden. The current target
    line shows a length hint (▓ characters). As users mark lines, they are
    revealed with syntax highlighting and a success/failure marker.

    For slots blocks, prompts are always visible and only answers are hidden.
    Header lines (without ::) are displayed but not drilled.

    State:
        current_line: Index of the drillable line being tested (reactive)
        line_results: List of bool results for revealed lines
        complete: True when all drillable lines have been revealed
    """

    DEFAULT_CSS = """
    RevealBlock {
        height: auto;
        margin: 1 0;
    }
    """

    current_line = reactive(0)

    def __init__(self, block: CodeBlock, block_num: int, total_blocks: int, id: str = None):
        super().__init__(id=id)
        self.block = block
        self.block_num = block_num
        self.total_blocks = total_blocks
        self.line_results: list[bool] = []
        self.complete = False

        # For slots blocks, parse lines and track drillable indices
        if block.block_type == "slots":
            self.slot_lines: list[SlotLine] = [parse_slot_line(line) for line in block.lines]
            self.drillable_indices: list[int] = [
                i for i, sl in enumerate(self.slot_lines) if sl.is_drillable
            ]
        else:
            self.slot_lines = []
            self.drillable_indices = list(range(len(block.lines)))

        # Check if block has any drillable content
        if not self.drillable_indices:
            self.complete = True
        
    def render(self) -> RenderableType:
        if self.block.block_type == "slots":
            return self._render_slots()
        else:
            return self._render_code()

    def _render_code(self) -> RenderableType:
        """Render a code block with line-by-line hidden content."""
        table = Table.grid(padding=(0, 2))
        table.add_column("Marker", justify="right", width=3)
        table.add_column("LineNo", justify="right", style="dim", width=4)
        table.add_column("Content", ratio=1)

        for i, line_content in enumerate(self.block.lines):
            line_no = str(i + 1)

            if i < len(self.line_results):
                # Revealed and graded
                success = self.line_results[i]
                marker = "✓" if success else "✗"
                marker_style = "green" if success else "red"

                # Syntax highlighting
                content = line_content.rstrip()
                if not content:
                    content = " "  # Empty line placeholder

                syntax = Syntax(content, self.block.language, theme="monokai", word_wrap=True)
                table.add_row(Text(marker, style=marker_style), line_no, syntax)

            elif i == self.current_line and not self.complete:
                # Current target (hidden) - show length hint
                length = len(line_content)
                hint = "▓" * min(length, 60)
                if length > 60:
                    hint += "..."
                if length == 0:
                    hint = "▓ (empty)"
                table.add_row("?", line_no, Text(hint, style="yellow dim"))

            else:
                # Future line (hidden)
                length = len(line_content)
                hint = "░" * min(length, 60)
                if length == 0:
                    hint = "░"
                table.add_row("", line_no, Text(hint, style="dim"))

        title = f"Block {self.block_num} of {self.total_blocks} ({self.block.language})"
        style = "blue"
        if self.complete:
            score = sum(self.line_results)
            total = len(self.line_results)
            pct = int(score / total * 100) if total > 0 else 100
            title += f" - DONE ({score}/{total} {pct}%)"
            style = "green" if pct == 100 else "yellow"

        return Panel(table, title=title, border_style=style)

    def _render_slots(self) -> RenderableType:
        """Render a slots block with prompts visible, answers hidden."""
        table = Table.grid(padding=(0, 2))
        table.add_column("Marker", justify="right", width=3)
        table.add_column("LineNo", justify="right", style="dim", width=4)
        table.add_column("Prompt", ratio=1)
        table.add_column("Answer", ratio=1)

        drillable_num = 0  # Counter for drillable lines only

        for i, slot in enumerate(self.slot_lines):
            if not slot.is_drillable:
                # Header/context line - show dimmed, no marker, no line number
                table.add_row("", "", Text(slot.prompt, style="dim italic"), Text(""))
                continue

            # This is a drillable line
            line_no = str(drillable_num + 1)

            if drillable_num < len(self.line_results):
                # Revealed and graded
                success = self.line_results[drillable_num]
                marker = "✓" if success else "✗"
                marker_style = "green" if success else "red"
                answer_style = "green" if success else "red"

                table.add_row(
                    Text(marker, style=marker_style),
                    line_no,
                    Text(slot.prompt, style="bold"),
                    Text(slot.answer or "", style=answer_style)
                )

            elif drillable_num == self.current_line and not self.complete:
                # Current target - prompt visible, answer hidden
                answer_len = len(slot.answer or "")
                hint = "▓" * min(answer_len, 30)
                if answer_len > 30:
                    hint += "..."
                if answer_len == 0:
                    hint = "▓"

                table.add_row(
                    Text("?", style="yellow"),
                    line_no,
                    Text(slot.prompt, style="bold yellow"),
                    Text(hint, style="yellow dim")
                )

            else:
                # Future line - prompt visible, answer hidden
                answer_len = len(slot.answer or "")
                hint = "░" * min(answer_len, 30)
                if answer_len == 0:
                    hint = "░"

                table.add_row(
                    "",
                    line_no,
                    Text(slot.prompt, style=""),
                    Text(hint, style="dim")
                )

            drillable_num += 1

        title = f"Block {self.block_num} of {self.total_blocks} (slots)"
        style = "cyan"
        if self.complete:
            score = sum(self.line_results)
            total = len(self.line_results)
            pct = int(score / total * 100) if total > 0 else 100
            title += f" - DONE ({score}/{total} {pct}%)"
            style = "green" if pct == 100 else "yellow"

        return Panel(table, title=title, border_style=style)

    def reveal_line(self, success: bool):
        """Mark current drillable line as success/fail and advance."""
        if self.complete:
            return

        self.line_results.append(success)
        self.current_line += 1

        if self.current_line >= len(self.drillable_indices):
            self.complete = True

    def skip_remaining(self):
        """Mark all remaining drillable lines as failed."""
        if self.complete:
            return

        remaining = len(self.drillable_indices) - len(self.line_results)
        self.line_results.extend([False] * remaining)
        self.current_line = len(self.drillable_indices)
        self.complete = True

    def get_result(self) -> BlockResult:
        """Return the BlockResult for this block.

        For slots blocks, only includes drillable lines in results.
        """
        if self.block.block_type == "slots":
            # Only return drillable lines
            drillable_lines = [self.block.lines[i] for i in self.drillable_indices]
            return BlockResult(
                lines=drillable_lines,
                results=self.line_results,
                quit=False
            )
        else:
            return BlockResult(
                lines=self.block.lines,
                results=self.line_results,
                quit=False
            )
