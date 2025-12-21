"""Dialogue screen for the reader - the core seminar interface."""
from datetime import datetime
from rich.markdown import Markdown

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Input, Label, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from reader.content import get_source_format, get_chapter_pdf, load_chapter
from reader.llm import get_provider
from reader.prompts import build_system_prompt, MODES
from reader.session import (
    Session,
    create_session,
    load_session,
    load_transcript,
    save_metadata,
    append_message,
)
from reader.config import load_config

# Mode colors for visual differentiation
MODE_COLORS = {
    "socratic": "cyan",
    "clarify": "green",
    "challenge": "red",
    "teach": "magenta",
    "quiz": "blue",
}

# Mode descriptions for selection UI
MODE_INFO = {
    "socratic": "Draw out understanding through questions",
    "clarify": "Get direct explanations when stuck",
    "challenge": "Stress-test claims with counterarguments",
    "teach": "Explain concepts to a confused student",
    "quiz": "Rapid-fire recall testing",
}


class ModeSelectModal(ModalScreen[str]):
    """Modal for selecting dialogue mode."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    ModeSelectModal {
        align: center middle;
    }

    #mode-select-container {
        width: 60;
        height: auto;
        max-height: 20;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    #mode-select-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #mode-list {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(self, current_mode: str) -> None:
        super().__init__()
        self.current_mode = current_mode

    def compose(self) -> ComposeResult:
        with Vertical(id="mode-select-container"):
            yield Label("Select Mode", id="mode-select-title")
            option_list = OptionList(id="mode-list")
            for mode in MODES:
                color = MODE_COLORS.get(mode, "white")
                desc = MODE_INFO.get(mode, "")
                # Mark current mode
                marker = " •" if mode == self.current_mode else ""
                prompt = f"[bold {color}]{mode}[/bold {color}]{marker}\n[dim]{desc}[/dim]"
                option_list.add_option(Option(prompt, id=mode))
            yield option_list

    def on_mount(self) -> None:
        # Focus the option list and highlight current mode
        option_list = self.query_one("#mode-list", OptionList)
        option_list.focus()
        # Find and highlight current mode
        for idx, mode in enumerate(MODES):
            if mode == self.current_mode:
                option_list.highlighted = idx
                break

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class DialogueScreen(Screen):
    """The main dialogue interface for reading sessions."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+m", "select_mode", "Mode"),
        Binding("ctrl+g", "generate_cards", "Cards"),
        Binding("ctrl+r", "record", "Voice"),
        Binding("ctrl+t", "toggle_tts", "TTS"),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        material_id: str,
        material_info: dict,
        chapter_num: int,
        chapter_title: str,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_info = material_info
        self.chapter_num = chapter_num
        self.chapter_title = chapter_title

        # Session state
        self.messages: list[dict] = []
        self.mode = "socratic"
        self.mode_index = 0
        self.source_format: str = "epub"  # 'pdf' or 'epub'
        self.chapter_content: str | None = None  # For EPUBs
        self.chapter_pdf: bytes | None = None  # For PDFs
        self.provider = None
        self.session: Session | None = None

        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.cache_size = 0  # Size of cached content (constant per session)
        self.using_cache = False

        # Voice input state
        self._recording = False
        self._voice_config = self._load_voice_config()

        # TTS state
        self._tts_enabled = False
        self._tts_config = self._load_tts_config()
        self._speaking = False

    def _load_voice_config(self) -> dict:
        """Load voice configuration from config.yaml."""
        try:
            config = load_config()
            return config.get("voice", {})
        except Exception:
            return {}

    def _load_tts_config(self) -> dict:
        """Load TTS configuration from config.yaml."""
        try:
            config = load_config()
            return config.get("tts", {})
        except Exception:
            return {}

    def compose(self) -> ComposeResult:
        book_title = self.material_info.get("title", self.material_id)

        yield Header()

        with Container(id="dialogue-container"):
            # Header info
            with Horizontal(id="dialogue-header"):
                yield Label(f"[bold]{book_title}[/bold]", id="book-title")
                yield Label(f"Chapter {self.chapter_num}: {self.chapter_title}", id="chapter-title")
                mode_color = MODE_COLORS.get(self.mode, "cyan")
                mode_desc = MODE_INFO.get(self.mode, "")
                yield Label(f"[{mode_color}]{self.mode}[/{mode_color}] [dim]{mode_desc}[/dim]", id="mode-indicator")
                yield Label("[dim]0 tokens[/dim]", id="token-counter")

            # Chat history
            yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)

            # Input area
            with Horizontal(id="input-area"):
                yield Input(placeholder="Type your message...", id="chat-input")

        yield Footer()

    def _build_system_prompt(self) -> str:
        """Build system prompt for current mode (content provided via cache)."""
        book_title = self.material_info.get("title", self.material_id)
        return build_system_prompt(
            mode=self.mode,
            book_title=book_title,
            chapter_title=f"Chapter {self.chapter_num}: {self.chapter_title}",
            session_phase="dialogue",
        )

    def _create_cache(self) -> bool:
        """Create or recreate the context cache. Returns True if successful."""
        if not self.provider:
            return False

        try:
            system_prompt = self._build_system_prompt()
            cache_name = self.provider.create_cache(
                system_prompt=system_prompt,
                chapter_content=self.chapter_content,
                chapter_pdf=self.chapter_pdf,
                ttl_seconds=900,
            )
            if cache_name:
                self.using_cache = True
                return True
            else:
                self.using_cache = False
                return False
        except Exception as e:
            self.notify(f"Cache error: {e}", severity="warning")
            self.using_cache = False
            return False

    def on_mount(self) -> None:
        """Initialize the dialogue session."""
        # Load chapter content based on source format
        self.source_format = get_source_format(self.material_id)

        if self.source_format == "pdf":
            self.chapter_pdf = get_chapter_pdf(self.material_id, self.chapter_num)
            self.chapter_content = None
        else:
            # EPUB: load pre-extracted text
            self.chapter_content = load_chapter(self.material_id, self.chapter_num)
            self.chapter_pdf = None

        # Load or create session
        existing_session = load_session(self.material_id, self.chapter_num)
        if existing_session:
            self.session = existing_session
            self._restore_session()
        else:
            self.session = create_session(
                self.material_id,
                self.chapter_num,
                self.chapter_title,
            )

        # Initialize LLM provider
        try:
            self.provider = get_provider()
        except Exception as e:
            self.notify(f"LLM error: {e}", severity="error")
            return

        # Create context cache (15 min TTL for testing)
        if self._create_cache():
            self.notify("Cache created", severity="information")
        else:
            self.notify("Running without cache", severity="warning")

        # Focus input
        self.query_one("#chat-input", Input).focus()

        # Show welcome message (only for new sessions)
        if not existing_session:
            chat_log = self.query_one("#chat-log", RichLog)
            chat_log.write("")
            chat_log.write("[bold cyan]Reader[/bold cyan]")
            chat_log.write(f"  Welcome to Chapter {self.chapter_num}: {self.chapter_title}")
            chat_log.write("  What would you like to explore?")
            chat_log.write("")

    def _restore_session(self) -> None:
        """Restore a previous session from transcript."""
        chat_log = self.query_one("#chat-log", RichLog)
        transcript = load_transcript(self.material_id, self.chapter_num)

        if not transcript:
            return

        chat_log.write("")
        chat_log.write("[dim]── Resuming session ──[/dim]")
        chat_log.write("")

        for msg in transcript:
            role = msg["role"]
            content = msg["content"]
            mode = msg.get("mode", "socratic")

            if role == "user":
                chat_log.write("[bold yellow]You[/bold yellow]")
                chat_log.write(f"  {content}")
            else:
                mode_color = MODE_COLORS.get(mode, "cyan")
                chat_log.write(f"[bold {mode_color}]Reader[/bold {mode_color}] [{mode_color}][{mode}][/{mode_color}]")
                chat_log.write(Markdown(content.strip()))

            chat_log.write("")

            # Rebuild messages list for LLM context
            self.messages.append({"role": role, "content": content})

        # Restore token counts and insights from session metadata
        if self.session:
            self.total_input_tokens = self.session.total_input_tokens
            self.total_output_tokens = self.session.total_output_tokens
            self.cache_size = self.session.cache_tokens
            self.update_token_display()

        chat_log.write("[dim]── Session resumed ──[/dim]")
        chat_log.write("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input immediately
        input_widget = self.query_one("#chat-input", Input)
        input_widget.value = ""

        # Show user message immediately
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write("[bold yellow]You[/bold yellow]")
        chat_log.write(f"  {user_input}")
        chat_log.write("")

        # Add to messages and persist
        self.messages.append({"role": "user", "content": user_input})
        append_message(
            self.material_id,
            self.chapter_num,
            role="user",
            content=user_input,
            mode=self.mode,
        )

        # Show thinking indicator immediately
        chat_log.write("[dim italic]  thinking...[/dim italic]")

        # Disable input while waiting
        input_widget.disabled = True

        # Get LLM response in background worker
        self.run_worker(self._fetch_response(), exclusive=True)

    async def _fetch_response(self) -> None:
        """Fetch LLM response in background worker."""
        import asyncio

        if not self.provider:
            self._show_error("LLM not configured")
            return

        # Cache is required - chapter content is only available via cache
        if not self.using_cache:
            self._show_error("Cache required but not available. Check provider configuration.")
            return
        system = None  # System prompt is baked into cache

        try:
            # Run blocking LLM call in thread pool
            chat_response = await asyncio.to_thread(
                self.provider.chat, self.messages, system
            )
            # Back on main event loop - safe to update UI
            self._show_response(chat_response)

        except Exception as e:
            self._show_error(str(e))

    def _show_response(self, chat_response) -> None:
        """Display LLM response (called from main thread)."""
        chat_log = self.query_one("#chat-log", RichLog)

        # Update token counts
        non_cached_input = chat_response.input_tokens - chat_response.cached_tokens
        self.total_input_tokens += non_cached_input
        self.total_output_tokens += chat_response.output_tokens
        if chat_response.cached_tokens > 0 and self.cache_size == 0:
            self.cache_size = chat_response.cached_tokens
        self.update_token_display()

        # Show response with mode badge
        mode_color = MODE_COLORS.get(self.mode, "cyan")
        chat_log.write(f"[bold {mode_color}]Reader[/bold {mode_color}] [{mode_color}][{self.mode}][/{mode_color}]")

        # Render response as markdown
        chat_log.write(Markdown(chat_response.text.strip()))

        chat_log.write("")  # Blank line after response

        # Add to messages and persist
        self.messages.append({"role": "assistant", "content": chat_response.text})
        append_message(
            self.material_id,
            self.chapter_num,
            role="assistant",
            content=chat_response.text,
            mode=self.mode,
            tokens={
                "input": chat_response.input_tokens,
                "output": chat_response.output_tokens,
                "cached": chat_response.cached_tokens,
            },
        )

        # Update session metadata
        if self.session:
            self.session.exchange_count += 1
            self.session.mode_distribution[self.mode] = (
                self.session.mode_distribution.get(self.mode, 0) + 1
            )
            self.session.total_input_tokens = self.total_input_tokens
            self.session.total_output_tokens = self.total_output_tokens
            self.session.cache_tokens = self.cache_size
            self.session.last_updated = datetime.now()
            save_metadata(self.session)

        # Re-enable input
        input_widget = self.query_one("#chat-input", Input)
        input_widget.disabled = False
        input_widget.focus()

        # Speak response if TTS enabled
        if self._tts_enabled:
            self.run_worker(
                self._speak_response(chat_response.text),
                exclusive=False,
                name="tts_speak",
            )

    async def _speak_response(self, text: str) -> None:
        """Speak the response text using TTS."""
        import asyncio

        try:
            voice = self._tts_config.get("voice", "af_heart")

            self._speaking = True

            def do_speak():
                from reader.tts import speak
                speed = self._tts_config.get("speed", 1.0)
                speak(text, voice=voice, speed=speed, strip_markdown=True)

            await asyncio.to_thread(do_speak)

        except ImportError as e:
            self.notify(f"TTS deps missing: {e}", severity="error")
        except Exception as e:
            self.notify(f"TTS error: {e}", severity="error")
        finally:
            self._speaking = False

    def _show_error(self, error_msg: str) -> None:
        """Display error message (called from main thread)."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[red]  Error: {error_msg}[/red]")
        chat_log.write("")

        # Re-enable input
        input_widget = self.query_one("#chat-input", Input)
        input_widget.disabled = False
        input_widget.focus()

    def update_token_display(self) -> None:
        """Update the token counter in the header."""
        def fmt(n: int) -> str:
            return f"{n / 1000:.1f}K" if n >= 1000 else str(n)

        # total_input_tokens is now conversation-only (cache subtracted)
        conversation = self.total_input_tokens + self.total_output_tokens

        if self.cache_size > 0:
            display = f"{fmt(conversation)} + {fmt(self.cache_size)} cached"
        else:
            display = f"{fmt(conversation)}"

        token_label = self.query_one("#token-counter", Label)
        token_label.update(f"[dim]{display}[/dim]")

    def action_select_mode(self) -> None:
        """Open mode selection modal."""
        self.app.push_screen(ModeSelectModal(self.mode), self.on_mode_selected)

    def on_mode_selected(self, mode: str | None) -> None:
        """Handle mode selection from modal."""
        if mode is None or mode == self.mode:
            return

        self.mode = mode
        self.mode_index = MODES.index(mode)

        # Update mode indicator with color and description
        mode_color = MODE_COLORS.get(self.mode, "cyan")
        mode_desc = MODE_INFO.get(self.mode, "")
        mode_label = self.query_one("#mode-indicator", Label)
        mode_label.update(f"[{mode_color}]{self.mode}[/{mode_color}] [dim]{mode_desc}[/dim]")

        # Recreate cache with new mode (system prompt includes mode)
        if self._create_cache():
            self.notify(f"Mode: {self.mode} (cache updated)", severity="information")
        else:
            self.notify(f"Mode: {self.mode}", severity="information")

        # Refocus input
        self.query_one("#chat-input", Input).focus()

    def action_record(self) -> None:
        """Toggle voice recording."""
        if not self._voice_config.get("enabled", True):
            self.notify("Voice input disabled in config", severity="warning")
            return

        if self._recording:
            # Stop recording early
            from reader.voice import stop_recording
            stop_recording()
            return

        # Run recording in background worker
        self.run_worker(self._record_voice(), exclusive=False, name="voice_recording")

    async def _record_voice(self) -> None:
        """Record and transcribe voice input."""
        import asyncio

        input_widget = self.query_one("#chat-input", Input)

        # Get voice config
        model_size = self._voice_config.get("model", "base")
        language = self._voice_config.get("language", "en")
        silence_threshold = self._voice_config.get("silence_threshold", 0.01)
        silence_duration = self._voice_config.get("silence_duration", 1.5)

        # Update UI to show recording
        self._recording = True
        original_placeholder = input_widget.placeholder
        input_widget.placeholder = "[Recording... Ctrl+R to finish]"
        input_widget.disabled = True

        try:
            # Import voice module (lazy to avoid import errors if deps missing)
            from reader.voice import record_and_transcribe

            # Run blocking recording in thread pool
            def do_record():
                return record_and_transcribe(
                    model_size=model_size,
                    language=language,
                    silence_threshold=silence_threshold,
                    silence_duration=silence_duration,
                )

            # Show transcribing state
            def on_transcribing():
                self.call_from_thread(
                    lambda: setattr(input_widget, "placeholder", "[Transcribing...]")
                )

            text = await asyncio.to_thread(do_record)

            # Update input with transcribed text
            if text:
                input_widget.value = text
                self.notify("Voice transcribed", severity="information")
            else:
                self.notify("No speech detected", severity="warning")

        except ImportError as e:
            self.notify(f"Voice deps missing: {e}", severity="error")
        except Exception as e:
            self.notify(f"Voice error: {e}", severity="error")
        finally:
            self._recording = False
            input_widget.placeholder = original_placeholder
            input_widget.disabled = False
            input_widget.focus()

    def action_toggle_tts(self) -> None:
        """Toggle text-to-speech for responses."""
        if not self._tts_config.get("enabled", True):
            self.notify("TTS disabled in config", severity="warning")
            return

        # If currently speaking, stop
        if self._speaking:
            try:
                from reader.tts import stop_speaking
                stop_speaking()
            except ImportError:
                pass
            self._speaking = False
            return

        # Toggle TTS
        self._tts_enabled = not self._tts_enabled
        status = "on" if self._tts_enabled else "off"
        self.notify(f"TTS {status}", severity="information")

    def action_generate_cards(self) -> None:
        """Generate drill cards from this session's transcript."""
        if not self.session:
            self.notify("No session to generate cards from", severity="warning")
            return

        if self.session.exchange_count == 0:
            self.notify("No dialogue yet - have a conversation first", severity="warning")
            return

        from .generate_cards import GenerateCardsScreen

        material_title = self.material_info.get("title", self.material_id)
        self.app.push_screen(
            GenerateCardsScreen(
                material_id=self.material_id,
                material_title=material_title,
                chapter_num=self.chapter_num,
                session=self.session,
            )
        )

    def action_back(self) -> None:
        """Go back to chapter selection."""
        # Stop any TTS playback
        if self._speaking:
            try:
                from reader.tts import stop_speaking
                stop_speaking()
            except ImportError:
                pass

        # Clean up cache
        if self.provider:
            self.provider.clear_cache()
        self.app.pop_screen()
