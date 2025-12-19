"""
Panel widgets for the unified dashboard.
"""
from datetime import datetime
from rich.console import RenderableType
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.progress_bar import ProgressBar as RichProgressBar
from textual.widget import Widget
from textual.widgets import Static

from reviewer.core import (
    get_todays_domain,
    get_next_task,
    get_sprint_progress,
    get_overall_progress,
    get_reviewer_summary,
    get_current_phase,
)


class TodayPanel(Widget):
    """Shows today's domain and next task."""
    
    DEFAULT_CSS = """
    TodayPanel {
        height: auto;
        padding: 0 1;
    }
    """
    
    def render(self) -> RenderableType:
        domain, override = get_todays_domain()
        next_task = get_next_task()
        
        content = Text()
        content.append("📚 Domain: ", style="bold")
        content.append(domain, style="yellow" if override else "green")
        content.append("\n")
        
        if override:
            content.append(f"   {override}", style="dim")
            content.append("\n")
        
        content.append("\n")
        content.append("📋 Next Task:\n", style="bold")
        
        if next_task:
            # Truncate if too long
            task_display = next_task[:60] + "..." if len(next_task) > 60 else next_task
            content.append(f"   {task_display}", style="cyan")
        else:
            content.append("   All tasks complete! 🎉", style="green")
        
        return Panel(content, title="TODAY", border_style="blue")


class ProgressPanel(Widget):
    """Shows sprint progress bars."""
    
    DEFAULT_CSS = """
    ProgressPanel {
        height: auto;
        padding: 0 1;
    }
    """
    
    def render(self) -> RenderableType:
        sprints = get_sprint_progress()
        done, total = get_overall_progress()
        
        table = Table.grid(padding=(0, 1))
        table.add_column("Sprint", width=12)
        table.add_column("Bar", width=12)
        table.add_column("Count", justify="right", width=6)
        
        for s in sprints:
            pct = s["done"] / s["total"] if s["total"] > 0 else 0
            filled = int(pct * 10)
            empty = 10 - filled
            
            if s["status"] == "complete":
                bar_style = "green"
            elif s["status"] == "in-progress":
                bar_style = "yellow"
            else:
                bar_style = "dim"
            
            bar = Text()
            bar.append("█" * filled, style=bar_style)
            bar.append("░" * empty, style="dim")
            
            # Truncate sprint name
            name = s["name"][:10] + ".." if len(s["name"]) > 12 else s["name"]
            
            table.add_row(
                Text(f"Sprint {s['num']}", style="bold"),
                bar,
                Text(f"{s['done']}/{s['total']}", style="dim")
            )
        
        # Overall
        if total > 0:
            pct = int(done / total * 100)
            table.add_row(Text(""), Text(""), Text(""))
            table.add_row(
                Text("Overall:", style="bold"),
                Text(""),
                Text(f"{done}/{total} ({pct}%)", style="cyan")
            )
        
        current_phase = get_current_phase()
        phase_name = current_phase.get("name", "PROGRESS").upper()
        return Panel(table, title=f"{phase_name} PROGRESS", border_style="blue")


class StatusPanel(Widget):
    """Shows reviewer status summary."""
    
    DEFAULT_CSS = """
    StatusPanel {
        height: auto;
        padding: 0 1;
    }
    """
    
    def render(self) -> RenderableType:
        summary = get_reviewer_summary()
        
        content = Text()
        
        # Status rows with color coding
        if summary["box_zero"] > 0:
            content.append("🔴 Box 0 (failed):    ", style="bold")
            content.append(f"{summary['box_zero']}", style="red")
            content.append("  ← Drill first!", style="dim italic")
            content.append("\n")
        
        if summary["overdue"] > 0:
            content.append("🟠 Overdue:           ", style="bold")
            content.append(f"{summary['overdue']}", style="yellow")
            content.append("\n")
        
        if summary["due_now"] > 0:
            content.append("🟡 Due now:           ", style="bold")
            content.append(f"{summary['due_now']}", style="yellow")
            content.append("\n")
        
        if summary["never_practiced"] > 0:
            content.append("⚪ Never practiced:   ", style="bold")
            content.append(f"{summary['never_practiced']}", style="dim")
            content.append("\n")
        
        total_due = summary["box_zero"] + summary["overdue"] + summary["due_now"]
        if total_due == 0 and summary["never_practiced"] == 0:
            content.append("✅ All caught up!", style="green bold")
            content.append("\n")
        
        content.append("─" * 35, style="dim")
        content.append("\n")
        
        content.append(f"📦 Total in focus/: ", style="bold")
        content.append(f"{summary['total_focus']}", style="cyan")
        
        if summary["last_practiced"]:
            last_date = summary["last_practiced"][:10]
            content.append(f"   │   Last: {last_date}", style="dim")
        
        return Panel(content, title="REVIEWER STATUS", border_style="blue")


class DrillListPanel(Widget):
    """Shows list of cards ready to drill with selection."""
    
    DEFAULT_CSS = """
    DrillListPanel {
        height: auto;
        min-height: 8;
        padding: 0 1;
    }
    """
    
    def __init__(self, drill_queue: list, selected_idx: int = 0, id: str = None):
        super().__init__(id=id)
        self.drill_queue = drill_queue
        self.selected_idx = selected_idx
    
    def render(self) -> RenderableType:
        if not self.drill_queue:
            content = Text("No cards due! All caught up. 🎉", style="green")
            return Panel(content, title="READY TO DRILL", border_style="green")
        
        table = Table.grid(padding=(0, 1))
        table.add_column("Sel", width=2)
        table.add_column("Name", width=25)
        table.add_column("Box", justify="center", width=7)
        table.add_column("Status", width=20)
        
        # Show up to 8 items
        display_count = min(8, len(self.drill_queue))
        
        for i in range(display_count):
            path, meta = self.drill_queue[i]
            is_selected = (i == self.selected_idx)
            
            # Selection marker
            sel = "▸" if is_selected else " "
            sel_style = "bold green" if is_selected else ""
            
            # Name
            name = path.stem
            if len(name) > 23:
                name = name[:20] + "..."
            
            # Box
            if meta["box"] is None:
                box_str = "new"
                box_style = "dim"
            elif meta["box"] == 0:
                box_str = "Box 0"
                box_style = "red"
            else:
                box_str = f"Box {meta['box']}"
                box_style = "cyan"
            
            # Status/due info
            due_info = meta["due_info"]
            if meta["status"] == "failed":
                due_style = "red"
            elif meta["status"] == "overdue":
                due_style = "yellow"
            elif meta["status"] == "new":
                due_style = "dim italic"
            else:
                due_style = "green"
            
            row_style = "reverse" if is_selected else ""
            
            table.add_row(
                Text(sel, style=sel_style),
                Text(name, style=f"{row_style}"),
                Text(box_str, style=box_style),
                Text(due_info, style=due_style)
            )
        
        if len(self.drill_queue) > display_count:
            remaining = len(self.drill_queue) - display_count
            table.add_row(
                Text(""),
                Text(f"... and {remaining} more", style="dim italic"),
                Text(""),
                Text("")
            )
        
        # Footer hint
        table.add_row(Text(""), Text(""), Text(""), Text(""))
        table.add_row(
            Text(""),
            Text("↑↓ navigate  │  Enter: drill", style="dim"),
            Text(""),
            Text("")
        )
        
        return Panel(table, title=f"READY TO DRILL ({len(self.drill_queue)})", border_style="green")
    
    def update_selection(self, new_idx: int):
        """Update selected index and refresh."""
        if self.drill_queue:
            self.selected_idx = max(0, min(new_idx, len(self.drill_queue) - 1))
            self.refresh()
    
    def get_selected_path(self):
        """Return the path of the currently selected item."""
        if self.drill_queue and 0 <= self.selected_idx < len(self.drill_queue):
            return self.drill_queue[self.selected_idx][0]
        return None
