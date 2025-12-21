from rich.console import RenderableType
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget
from textual.reactive import reactive

from knos.reviewer.core import CodeBlock, BlockResult

class RevealBlock(Widget):
    """
    A widget that displays a code block and allows line-by-line revealing.
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
        
    def render(self) -> RenderableType:
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
                # We strip newline to avoid extra spacing in table
                content = line_content.rstrip()
                if not content:
                    content = " " # Empty line placeholder
                
                syntax = Syntax(content, self.block.language, theme="monokai", word_wrap=True)
                
                table.add_row(Text(marker, style=marker_style), line_no, syntax)
                
            elif i == self.current_line and not self.complete:
                # Current target (hidden)
                # Show length hint
                length = len(line_content)
                hint = "▓" * min(length, 60)
                if length > 60:
                    hint += "..."
                if length == 0:
                    hint = "▓ (empty)"
                    
                table.add_row("?", line_no, Text(hint, style="yellow dim"))
                
            else:
                # Future line (hidden) or skipped
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
            pct = int(score/total*100) if total > 0 else 100
            title += f" - DONE ({score}/{total} {pct}%)"
            style = "green" if pct == 100 else "yellow"
            
        return Panel(table, title=title, border_style=style)

    def reveal_line(self, success: bool):
        """Mark current line as success/fail and advance."""
        if self.complete:
            return
            
        self.line_results.append(success)
        self.current_line += 1
        
        if self.current_line >= len(self.block.lines):
            self.complete = True
            # Trigger event? For now just let parent check

    def skip_remaining(self):
        """Mark all remaining lines as failed."""
        if self.complete:
            return
            
        remaining = len(self.block.lines) - len(self.line_results)
        self.line_results.extend([False] * remaining)
        self.current_line = len(self.block.lines)
        self.complete = True

    def get_result(self) -> BlockResult:
        """Return the BlockResult for this block."""
        return BlockResult(
            lines=self.block.lines,
            results=self.line_results,
            quit=False
        )
