"""Card generation screen - generates drill cards from session transcripts."""
import re
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, RichLog, Static
from textual.containers import Container
from textual.binding import Binding

from reader.content import ContentId, get_chapter_text, format_content_id
from reader.session import Session, load_transcript, _content_id_to_prefix
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


def extract_card_title(card_content: str) -> str:
    """Extract title from card content."""
    first_line = card_content.split("\n")[0]
    return re.sub(r"^#+\s*", "", first_line).strip()


def generate_filename(card_content: str, index: int) -> str:
    """Generate a filename from card title."""
    title = extract_card_title(card_content)
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
        content_id: ContentId,
        session: Session,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_title = material_title
        self.content_id = content_id
        self.session = session

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="generate-container"):
            yield Label(
                f"[bold]Generating Cards[/bold] · {self.material_title} {format_content_id(self.content_id)}",
                id="generate-header",
            )
            yield RichLog(id="generate-log", wrap=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Start generation process."""
        self.run_worker(self._generate_cards(), exclusive=True)

    async def _generate_cards(self) -> None:
        """Generate cards from session transcript with streaming progress."""
        import asyncio

        log = self.query_one("#generate-log", RichLog)

        log.write("[dim]Loading content...[/dim]")
        chapter_content = get_chapter_text(self.material_id, self.content_id)
        log.write(f"  Content: {len(chapter_content):,} chars")

        log.write("[dim]Loading transcript...[/dim]")
        transcript = load_transcript(self.material_id, self.content_id)
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

        log.write("")
        log.write("[dim]Generating cards...[/dim]")

        try:
            provider = get_provider()

            # Stream the response and detect cards as they're generated
            def stream_and_parse():
                """Run streaming in thread, return cards as they're found."""
                buffer = ""
                cards_found = []

                for chunk in provider.stream_chat(
                    [{"role": "user", "content": user_message}],
                    system_prompt,
                ):
                    buffer += chunk

                    # Check if we have a complete card (delimiter followed by content)
                    while "===CARD===" in buffer:
                        parts = buffer.split("===CARD===", 1)
                        before = parts[0].strip()
                        after = parts[1] if len(parts) > 1 else ""

                        # If there's content before the delimiter, it's a card
                        if before and before.startswith("#"):
                            cards_found.append(before)
                            # Notify UI of new card
                            title = extract_card_title(before)
                            self.app.call_from_thread(
                                log.write,
                                f"  [green]✓[/green] Found: [bold]{title}[/bold]"
                            )

                        buffer = after

                # Handle final card (after last delimiter or if no delimiters)
                final = buffer.strip()
                if final and final.startswith("#"):
                    cards_found.append(final)
                    title = extract_card_title(final)
                    self.app.call_from_thread(
                        log.write,
                        f"  [green]✓[/green] Found: [bold]{title}[/bold]"
                    )

                return cards_found

            cards = await asyncio.to_thread(stream_and_parse)

            log.write("")

            if not cards:
                log.write("[yellow]No cards generated[/yellow]")
                return

            log.write(f"[bold]Writing {len(cards)} cards...[/bold]")

            # Write cards to drafts directory
            content_prefix = _content_id_to_prefix(self.content_id)
            drafts_dir = DRAFTS_DIR / self.material_id / content_prefix
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
                log.write(f"  [dim]{filename}[/dim]")

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
