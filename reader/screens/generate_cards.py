"""Card generation screen - generates drill cards from session transcripts."""
import re
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, RichLog, Static
from textual.containers import Container
from textual.binding import Binding

from reader.content import get_chapter_text
from reader.session import Session, load_transcript
from reader.llm import get_provider
from reader.prompts import load_prompt

# Output directory for card drafts
DRAFTS_DIR = Path(__file__).parent.parent / "drafts"


def parse_cards(response: str) -> list[str]:
    """Parse LLM response into individual card contents."""
    # Split on ===CARD=== delimiter
    parts = re.split(r"===CARD===", response)

    cards = []
    for part in parts:
        content = part.strip()
        if content and content.startswith("#"):
            cards.append(content)

    return cards


def generate_filename(card_content: str, index: int) -> str:
    """Generate a filename from card title."""
    # Extract title from first line
    first_line = card_content.split("\n")[0]
    # Remove markdown heading prefix
    title = re.sub(r"^#+\s*", "", first_line)
    # Convert to snake_case filename
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "_", slug).strip("_")

    if not slug:
        slug = f"card_{index}"

    return f"{slug}.md"


class GenerateCardsScreen(Screen):
    """Screen for generating cards from a session."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        material_id: str,
        material_title: str,
        chapter_num: int,
        session: Session,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_title = material_title
        self.chapter_num = chapter_num
        self.session = session

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="generate-container"):
            yield Label(
                f"[bold]Generating Cards[/bold] · {self.material_title} Ch.{self.chapter_num}",
                id="generate-header",
            )
            yield RichLog(id="generate-log", wrap=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Start generation process."""
        self.run_worker(self._generate_cards(), exclusive=True)

    async def _generate_cards(self) -> None:
        """Generate cards from session transcript."""
        import asyncio

        log = self.query_one("#generate-log", RichLog)

        log.write("[dim]Loading chapter content...[/dim]")
        chapter_content = get_chapter_text(self.material_id, self.chapter_num)
        log.write(f"  Chapter: {len(chapter_content):,} chars")

        log.write("[dim]Loading transcript...[/dim]")
        transcript = load_transcript(self.material_id, self.chapter_num)
        log.write(f"  Transcript: {len(transcript)} messages")

        if not transcript:
            log.write("[red]No transcript found for this session[/red]")
            return

        # Format transcript for LLM
        transcript_text = self._format_transcript(transcript)

        log.write("[dim]Loading card generation prompt...[/dim]")
        system_prompt = load_prompt("card_generation")

        # Build user message with chapter + transcript
        user_message = f"""## Chapter Content

{chapter_content}

---

## Dialogue Transcript

{transcript_text}

---

Generate drill cards based on the concepts the user engaged with in this dialogue."""

        log.write("[dim]Calling LLM...[/dim]")
        log.write("")

        try:
            provider = get_provider()

            # Call LLM
            response = await asyncio.to_thread(
                provider.chat,
                [{"role": "user", "content": user_message}],
                system_prompt,
            )

            log.write(f"[green]Response received[/green] ({response.output_tokens} tokens)")
            log.write("")

            # Parse cards from response
            cards = parse_cards(response.text)
            log.write(f"[bold]Parsed {len(cards)} cards[/bold]")
            log.write("")

            if not cards:
                log.write("[yellow]No cards found in response[/yellow]")
                log.write("[dim]Raw response:[/dim]")
                log.write(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                return

            # Write cards to drafts directory
            drafts_dir = DRAFTS_DIR / self.material_id / f"ch{self.chapter_num:02d}"
            drafts_dir.mkdir(parents=True, exist_ok=True)

            for i, card_content in enumerate(cards, 1):
                filename = generate_filename(card_content, i)
                filepath = drafts_dir / filename

                # Avoid overwriting - add timestamp if exists
                if filepath.exists():
                    timestamp = datetime.now().strftime("%H%M%S")
                    stem = filepath.stem
                    filepath = drafts_dir / f"{stem}_{timestamp}.md"

                filepath.write_text(card_content)

                # Show card preview
                title = card_content.split("\n")[0]
                log.write(f"  [green]✓[/green] {filename}")
                log.write(f"    {title}")

            log.write("")
            log.write(f"[bold green]Done![/bold green] Cards written to:")
            try:
                display_path = drafts_dir.relative_to(Path.cwd())
            except ValueError:
                display_path = drafts_dir
            log.write(f"  [cyan]{display_path}[/cyan]")

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    def _format_transcript(self, transcript: list[dict]) -> str:
        """Format transcript messages for LLM context."""
        lines = []
        for msg in transcript:
            role = msg["role"].upper()
            mode = msg.get("mode", "")
            content = msg["content"]

            if role == "ASSISTANT" and mode:
                lines.append(f"**{role}** [{mode}]:\n{content}\n")
            else:
                lines.append(f"**{role}**:\n{content}\n")

        return "\n".join(lines)

    def action_back(self) -> None:
        """Go back to session browser."""
        self.app.pop_screen()
