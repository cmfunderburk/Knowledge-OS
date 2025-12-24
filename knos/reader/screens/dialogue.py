"""Dialogue screen for the reader - the core seminar interface."""
from datetime import datetime
from rich.markdown import Markdown

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Input, Label, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from knos.reader.content import ContentId, get_source_format, get_chapter_pdf, load_chapter, format_content_id, get_article_text, get_article_pdf
from knos.reader.config import get_material_type
from knos.reader.llm import get_provider
from knos.reader.prompts import build_cache_prompt, get_mode_instruction, MODES
from knos.reader.session import (
    Session,
    create_session,
    load_session,
    load_transcript,
    save_metadata,
    append_message,
)
from knos.reader.config import load_config

# Mode colors for visual differentiation
MODE_COLORS = {
    "socratic": "cyan",
    "clarify": "green",
    "challenge": "red",
    "teach": "magenta",
    "quiz": "blue",
    "technical": "yellow",
}

# Mode descriptions for selection UI
MODE_INFO = {
    "socratic": "Draw out understanding through questions",
    "clarify": "Get direct explanations when stuck",
    "challenge": "Stress-test claims with counterarguments",
    "teach": "Explain concepts to a confused student",
    "quiz": "Rapid-fire recall testing",
    "technical": "Step-by-step guidance through formulas and procedures",
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
        chapter_num: ContentId | None,  # int for chapters, str for appendices, None for articles
        chapter_title: str,
    ) -> None:
        super().__init__()
        self.material_id = material_id
        self.material_info = material_info
        self.chapter_num = chapter_num  # ContentId | None - kept as chapter_num for compatibility
        self.chapter_title = chapter_title
        self.is_article = get_material_type(material_id) == "article"

        # Session state
        self.messages: list[dict] = []
        self.mode = "socratic"
        self.mode_index = 0
        self.source_format: str = "epub"  # 'pdf' or 'epub'
        self.chapter_content: str | None = None  # For EPUBs
        self.chapter_pdf: bytes | None = None  # For PDFs
        self.provider = None
        self.session: Session | None = None

        # Token tracking (for display: context window, not cumulative)
        self.context_window_size = 0  # Last request's total input tokens
        self.cache_size = 0  # Size of cached content (constant per session)
        self.using_cache = False
        self._system_prompt: str | None = None  # For non-cached article mode
        self._setup_error: str | None = None  # Error message from setup failure

        # Voice input state
        self._recording = False
        self._voice_config = self._load_voice_config()

        # TTS state - respect config.enabled setting
        self._tts_config = self._load_tts_config()
        self._tts_enabled = self._tts_config.get("enabled", True)
        self._speaking = False

        # Session config
        self._session_config = self._load_session_config()

        # Cache timer state
        self._cache_created_at: datetime | None = None
        self._cache_duration_minutes: int = self._session_config.get("duration_minutes", 30)
        self._cache_timer_interval = None

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

    def _load_session_config(self) -> dict:
        """Load session configuration from config.yaml."""
        try:
            config = load_config()
            return config.get("session", {})
        except Exception:
            return {}

    def compose(self) -> ComposeResult:
        book_title = self.material_info.get("title", self.material_id)

        yield Header()

        with Container(id="dialogue-container"):
            # Header info
            with Horizontal(id="dialogue-header"):
                yield Label(f"[bold]{book_title}[/bold]", id="book-title")
                if self.is_article:
                    # Articles show author instead of chapter
                    author = self.material_info.get("author", "")
                    yield Label(f"[dim]{author}[/dim]", id="chapter-title")
                else:
                    content_label = format_content_id(self.chapter_num)
                    yield Label(f"{content_label}: {self.chapter_title}", id="chapter-title")
                mode_color = MODE_COLORS.get(self.mode, "cyan")
                mode_desc = MODE_INFO.get(self.mode, "")
                yield Label(f"[{mode_color}]{self.mode}[/{mode_color}] [dim]{mode_desc}[/dim]", id="mode-indicator")
                yield Label("", id="cache-timer")
                yield Label("[dim]0 tokens[/dim]", id="token-counter")

            # Chat history
            yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)

            # Input area
            with Horizontal(id="input-area"):
                yield Input(placeholder="Type your message...", id="chat-input")

        yield Footer()

    def _build_cache_prompt(self) -> str:
        """Build system prompt for cache (mode-agnostic)."""
        book_title = self.material_info.get("title", self.material_id)
        if self.is_article:
            # For articles, use title directly (no chapter prefix)
            return build_cache_prompt(
                book_title=book_title,
                chapter_title=self.chapter_title,
            )
        else:
            content_label = format_content_id(self.chapter_num)
            return build_cache_prompt(
                book_title=book_title,
                chapter_title=f"{content_label}: {self.chapter_title}",
            )

    def _create_cache(self) -> bool:
        """Create the context cache. Only called once per session.

        For EPUB articles that are too short for caching, falls back to
        including content in the system prompt for each request.
        PDF articles always use the cache (Gemini reads PDFs natively).
        """
        if not self.provider:
            return False

        system_prompt = self._build_cache_prompt()

        # Fallback only works for text content (EPUB articles), not PDFs
        can_fallback = self.is_article and self.chapter_content is not None

        def _setup_article_fallback():
            """Set up non-cached article mode (EPUB only)."""
            self.using_cache = False
            self._system_prompt = (
                f"{system_prompt}\n\n"
                f"<article>\n{self.chapter_content}\n</article>"
            )

        try:
            # Get configured duration (default 30 minutes)
            duration_minutes = self._session_config.get("duration_minutes", 30)
            ttl_seconds = duration_minutes * 60

            cache_name = self.provider.create_cache(
                system_prompt=system_prompt,
                chapter_content=self.chapter_content,
                chapter_pdf=self.chapter_pdf,
                ttl_seconds=ttl_seconds,
            )
            if cache_name:
                self.using_cache = True
                return True
            else:
                # Cache not created (content too small)
                if can_fallback:
                    _setup_article_fallback()
                    return True
                self.using_cache = False
                return False
        except Exception as e:
            # Cache creation failed - EPUB articles can still proceed without cache
            if can_fallback:
                _setup_article_fallback()
                return True
            self.using_cache = False
            self._setup_error = str(e)
            return False

    def _inject_mode_context(self, messages: list[dict]) -> list[dict]:
        """
        Inject mode instruction into the first user message.

        Returns a new list with mode context prepended to the first user message.
        """
        if not messages:
            return messages

        # Get mode instruction
        mode_instruction = get_mode_instruction(self.mode)

        # Create modified messages list
        modified = []
        mode_injected = False

        for msg in messages:
            if msg["role"] == "user" and not mode_injected:
                # Prepend mode context to first user message
                mode_prefix = f"[MODE: {self.mode}]\n\n{mode_instruction}\n\n---\n\n"
                modified.append({
                    "role": "user",
                    "content": mode_prefix + msg["content"]
                })
                mode_injected = True
            else:
                modified.append(msg)

        return modified

    def on_mount(self) -> None:
        """Initialize the dialogue session."""
        # Show loading state immediately
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write("")
        chat_log.write("[dim]Preparing session...[/dim]")

        # Disable input while loading
        input_widget = self.query_one("#chat-input", Input)
        input_widget.disabled = True

        # Run initialization in background
        self.run_worker(self._initialize_session(), exclusive=True)

    async def _initialize_session(self) -> None:
        """Initialize session in background (cache creation + opening prompt)."""
        import asyncio

        chat_log = self.query_one("#chat-log", RichLog)
        input_widget = self.query_one("#chat-input", Input)

        # Load content based on material type and source format
        self.source_format = get_source_format(self.material_id)

        if self.is_article:
            # Articles: use PDF bytes for PDFs, text for EPUBs
            if self.source_format == "pdf":
                self.chapter_pdf = get_article_pdf(self.material_id)
                self.chapter_content = None
            else:
                self.chapter_content = get_article_text(self.material_id)
                self.chapter_pdf = None
        elif self.source_format == "pdf":
            self.chapter_pdf = get_chapter_pdf(self.material_id, self.chapter_num)
            self.chapter_content = None
        else:
            self.chapter_content = load_chapter(self.material_id, self.chapter_num)
            self.chapter_pdf = None

        # Load or create session (don't restore yet - we'll do that after cache is ready)
        existing_session = load_session(self.material_id, self.chapter_num)
        if existing_session:
            self.session = existing_session
            # Load messages into memory but don't display yet
            self._load_session_messages()
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
            chat_log.write(f"[red]LLM error: {e}[/red]")
            return

        # Create context cache (blocking operation - runs in thread pool)
        cache_success = await asyncio.to_thread(self._create_cache)

        if not cache_success:
            if self._setup_error and "API key" in self._setup_error:
                chat_log.write("[red]API key invalid or expired.[/red]")
                chat_log.write("[dim]Update key in config/reader.yaml or set GOOGLE_API_KEY env var.[/dim]")
                chat_log.write("[dim]Run 'knos read test' to verify configuration.[/dim]")
            elif self._setup_error:
                chat_log.write(f"[red]Session setup failed: {self._setup_error}[/red]")
            else:
                chat_log.write("[red]Session setup failed. Cannot proceed.[/red]")
            return

        # Start cache expiration timer (only if using actual cache, not system prompt fallback)
        if self.using_cache:
            self._start_cache_timer()

        # Clear loading messages and prepare display
        chat_log.clear()

        # Build opening prompt based on session state
        book_title = self.material_info.get("title", self.material_id)
        is_resumed = existing_session and existing_session.exchange_count > 0

        # For resumed sessions, display the previous conversation first
        if is_resumed:
            self._display_transcript()
            self.update_token_display()
        else:
            chat_log.write("")

        # Detect if last session was just opened and closed without real conversation
        last_session_empty = False
        if is_resumed:
            last_session_empty = self._was_last_session_empty()

        # Build content reference based on type
        if self.is_article:
            author = self.material_info.get("author", "")
            content_ref = f"the article \"{book_title}\" by {author}" if author else f"the article \"{book_title}\""
        else:
            content_label = format_content_id(self.chapter_num)
            content_ref = f"{content_label}: {self.chapter_title} from {book_title}"

        if is_resumed:
            if last_session_empty:
                # User opened session previously but left without engaging
                opening_prompt = (
                    f"I'm returning to {content_ref}. "
                    f"Note: I opened this session before but got distracted and left without "
                    f"actually engaging with the material. This is effectively a fresh start. "
                    f"Can you help orient me to what this {'article' if self.is_article else 'section'} covers and suggest "
                    f"how we might approach it together?"
                )
            else:
                # Resumed session with real prior conversation
                opening_prompt = (
                    f"I'm returning to continue our discussion of {content_ref}. "
                    f"We've had {existing_session.exchange_count} exchanges so far. "
                    f"Based on our previous conversation, what direction would you suggest "
                    f"we go from here, or what might be worth revisiting?"
                )
        else:
            # New session - introduce the material
            opening_prompt = (
                f"Hello! I'm beginning to read {content_ref}. "
                f"This is my first time engaging with this material. "
                f"Can you help orient me to what this {'article' if self.is_article else 'section'} covers and suggest "
                f"how we might approach it together?"
            )

        # Send opening prompt (hidden from user) and get LLM response
        if is_resumed:
            chat_log.write("[dim italic]  reviewing our discussion...[/dim italic]")
        else:
            chat_log.write("[dim italic]  thinking...[/dim italic]")

        # Build messages for opening exchange
        # For resumed sessions, include history for context but opening prompt is ephemeral
        if is_resumed:
            # Append opening prompt to existing conversation for LLM context
            opening_messages = self.messages + [{"role": "user", "content": opening_prompt}]
        else:
            opening_messages = [{"role": "user", "content": opening_prompt}]

        messages_with_mode = self._inject_mode_context(opening_messages)

        try:
            # Use system prompt for non-cached articles, None for cached content
            system = self._system_prompt if not self.using_cache else None
            chat_response = await asyncio.to_thread(
                self.provider.chat, messages_with_mode, system
            )

            # For resumed sessions, preserve the transcript history
            # For new sessions, clear loading messages
            if is_resumed:
                # Just add a separator after the "thinking..." line
                chat_log.write("")
            else:
                chat_log.clear()
                chat_log.write("")

            # Display LLM response as opening message
            mode_color = MODE_COLORS.get(self.mode, "cyan")
            chat_log.write(f"[bold {mode_color}]Reader[/bold {mode_color}] [{mode_color}][{self.mode}][/{mode_color}]")
            chat_log.write(Markdown(chat_response.text.strip()))
            chat_log.write("")

            # Persist opening exchange to transcript (both new and resumed sessions)
            self.messages.append({"role": "user", "content": opening_prompt})
            self.messages.append({"role": "assistant", "content": chat_response.text})

            append_message(
                self.material_id, self.chapter_num,
                role="user", content=opening_prompt, mode=self.mode,
            )
            append_message(
                self.material_id, self.chapter_num,
                role="assistant", content=chat_response.text, mode=self.mode,
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
                non_cached = chat_response.input_tokens - chat_response.cached_tokens
                self.session.total_input_tokens += non_cached
                self.session.total_output_tokens += chat_response.output_tokens
                if chat_response.cached_tokens > 0:
                    self.session.cache_tokens = chat_response.cached_tokens
                self.session.last_updated = datetime.now()
                save_metadata(self.session)

            # Update token display (context window = total input for this request)
            self.context_window_size = chat_response.input_tokens
            if chat_response.cached_tokens > 0:
                self.cache_size = chat_response.cached_tokens
            self.update_token_display()

            # Speak opening response if TTS enabled
            if self._tts_enabled:
                self.run_worker(
                    self._speak_response(chat_response.text),
                    exclusive=False,
                    name="tts_opening",
                )

        except Exception as e:
            chat_log.write(f"[red]Error getting opening response: {e}[/red]")

        # Enable input and focus
        input_widget.disabled = False
        input_widget.focus()

    def _load_session_messages(self) -> None:
        """Load session transcript into memory (without displaying)."""
        transcript = load_transcript(self.material_id, self.chapter_num)

        for msg in transcript:
            role = msg["role"]
            content = msg["content"]
            self.messages.append({"role": role, "content": content})

        # Restore cache size from session metadata
        # (context_window_size will be set on next API call)
        if self.session:
            self.cache_size = self.session.cache_tokens

    def _was_last_session_empty(self) -> bool:
        """
        Check if the last session was just opened and closed without real engagement.

        Returns True if all user messages in the transcript are system-generated
        opening prompts (not actual user input).
        """
        user_messages = [msg["content"] for msg in self.messages if msg["role"] == "user"]

        if not user_messages:
            return True

        # If any user message is not an opening prompt, real conversation happened
        for content in user_messages:
            if not self._is_opening_prompt(content):
                return False

        return True

    def _is_opening_prompt(self, content: str) -> bool:
        """Check if a message is a system-generated opening prompt."""
        opening_patterns = [
            "Hello! I'm beginning to read",
            "I'm returning to continue our discussion",
            "I'm returning to",  # Catches the "distracted" variant too
        ]
        return any(content.startswith(pattern) for pattern in opening_patterns)

    def _display_transcript(self) -> None:
        """Display the session transcript in the chat log."""
        chat_log = self.query_one("#chat-log", RichLog)
        transcript = load_transcript(self.material_id, self.chapter_num)

        if not transcript:
            return

        chat_log.write("[dim]── Previous conversation ──[/dim]")
        chat_log.write("")

        # Track whether to skip the next assistant message (response to hidden prompt)
        skip_next_assistant = False

        for msg in transcript:
            role = msg["role"]
            content = msg["content"]
            mode = msg.get("mode", "socratic")

            if role == "user":
                # Hide system-generated opening prompts
                if self._is_opening_prompt(content):
                    skip_next_assistant = True
                    continue

                chat_log.write("[bold yellow]You[/bold yellow]")
                chat_log.write(f"  {content}")
            else:
                # Skip LLM responses to hidden opening prompts
                if skip_next_assistant:
                    skip_next_assistant = False
                    continue

                mode_color = MODE_COLORS.get(mode, "cyan")
                chat_log.write(f"[bold {mode_color}]Reader[/bold {mode_color}] [{mode_color}][{mode}][/{mode_color}]")
                chat_log.write(Markdown(content.strip()))

            chat_log.write("")

        chat_log.write("[dim]── Continuing ──[/dim]")
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

        # Cache is required for books; articles can use system prompt fallback
        if not self.using_cache and not self._system_prompt:
            self._show_error("Cache required but not available. Check provider configuration.")
            return

        # Inject mode instructions into messages (mode-specific behavior without cache recreation)
        messages_with_mode = self._inject_mode_context(self.messages)

        try:
            # Run blocking LLM call in thread pool
            # Use system prompt for non-cached articles, None for cached content
            system = self._system_prompt if not self.using_cache else None
            chat_response = await asyncio.to_thread(
                self.provider.chat, messages_with_mode, system
            )
            # Back on main event loop - safe to update UI
            self._show_response(chat_response)

        except Exception as e:
            self._show_error(str(e))

    def _show_response(self, chat_response) -> None:
        """Display LLM response (called from main thread)."""
        chat_log = self.query_one("#chat-log", RichLog)

        # Update token display (context window = total input for this request)
        self.context_window_size = chat_response.input_tokens
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

        # Update session metadata (cumulative tokens for analytics)
        if self.session:
            self.session.exchange_count += 1
            self.session.mode_distribution[self.mode] = (
                self.session.mode_distribution.get(self.mode, 0) + 1
            )
            non_cached = chat_response.input_tokens - chat_response.cached_tokens
            self.session.total_input_tokens += non_cached
            self.session.total_output_tokens += chat_response.output_tokens
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
            speed = self._tts_config.get("speed", 1.0)
            short_text_threshold = self._tts_config.get("short_text_threshold", 200)
            target_chunk_size = self._tts_config.get("target_chunk_size", 350)
            max_chunk_size = self._tts_config.get("max_chunk_size", 500)

            self._speaking = True

            def do_speak():
                from knos.reader.tts import speak
                speak(
                    text,
                    voice=voice,
                    speed=speed,
                    strip_markdown=True,
                    short_text_threshold=short_text_threshold,
                    target_chunk_size=target_chunk_size,
                    max_chunk_size=max_chunk_size,
                )

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

        # Show context window size (total input tokens for last request)
        if self.context_window_size > 0:
            if self.cache_size > 0:
                display = f"{fmt(self.context_window_size)} ctx ({fmt(self.cache_size)} cached)"
            else:
                display = f"{fmt(self.context_window_size)} ctx"
        else:
            display = "0 tokens"

        token_label = self.query_one("#token-counter", Label)
        token_label.update(f"[dim]{display}[/dim]")

    def _start_cache_timer(self) -> None:
        """Start the cache expiration timer."""
        self._cache_created_at = datetime.now()
        self._update_cache_timer()
        # Update every 30 seconds
        self._cache_timer_interval = self.set_interval(30, self._update_cache_timer)

    def _update_cache_timer(self) -> None:
        """Update the cache timer display."""
        if not self._cache_created_at:
            return

        elapsed = datetime.now() - self._cache_created_at
        remaining_seconds = (self._cache_duration_minutes * 60) - elapsed.total_seconds()

        timer_label = self.query_one("#cache-timer", Label)

        if remaining_seconds <= 0:
            # Cache expired
            timer_label.update("[red bold]cache expired[/red bold]")
            self._handle_cache_expired()
        elif remaining_seconds <= 300:  # 5 minutes warning
            mins = int(remaining_seconds // 60)
            secs = int(remaining_seconds % 60)
            timer_label.update(f"[yellow]{mins}:{secs:02d} left[/yellow]")
        else:
            mins = int(remaining_seconds // 60)
            timer_label.update(f"[dim]{mins}m left[/dim]")

    def _handle_cache_expired(self) -> None:
        """Handle cache expiration - disable input and notify user."""
        if self._cache_timer_interval:
            self._cache_timer_interval.stop()
            self._cache_timer_interval = None

        input_widget = self.query_one("#chat-input", Input)
        input_widget.disabled = True
        input_widget.placeholder = "Session expired - press Escape to restart"
        self.notify("Cache expired. Exit and re-enter to continue.", severity="warning")

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

        # Mode is injected into messages, no cache recreation needed
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
            from knos.reader.voice import stop_recording
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
            from knos.reader.voice import record_and_transcribe

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
                from knos.reader.tts import stop_speaking
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
                content_id=self.chapter_num,
                session=self.session,
            )
        )

    def action_back(self) -> None:
        """Go back to chapter selection."""
        # Stop any TTS playback and unload model to free VRAM
        if self._speaking:
            try:
                from knos.reader.tts import stop_speaking
                stop_speaking()
            except ImportError:
                pass

        try:
            from knos.reader.tts import unload_backend
            unload_backend()
        except ImportError:
            pass

        # Stop cache timer
        if self._cache_timer_interval:
            self._cache_timer_interval.stop()
            self._cache_timer_interval = None

        # Clean up cache
        if self.provider:
            self.provider.clear_cache()
        self.app.pop_screen()
