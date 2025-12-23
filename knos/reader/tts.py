"""Text-to-speech module using Kokoro for high-quality local neural TTS.

Requires optional voice dependencies: uv sync --extra voice
"""
import queue
import re
import threading
import warnings
from typing import Callable

# Suppress warnings from ML libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Preload NVIDIA libraries (must happen before importing torch/kokoro)
from knos.reader.cuda_utils import is_cuda_available  # noqa: E402

# Check if TTS dependencies are available
_tts_available: bool | None = None


def is_tts_available() -> bool:
    """Check if TTS dependencies are installed."""
    global _tts_available
    if _tts_available is not None:
        return _tts_available

    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        import kokoro  # noqa: F401
        _tts_available = True
    except ImportError:
        _tts_available = False

    return _tts_available


# Lazy imports for optional dependencies
np = None
sd = None


def _ensure_tts_deps():
    """Import TTS dependencies, raising ImportError if not available."""
    global np, sd
    if np is None:
        if not is_tts_available():
            raise ImportError(
                "TTS requires optional dependencies. "
                "Install with: uv sync --extra voice"
            )
        import numpy
        import sounddevice
        np = numpy
        sd = sounddevice

# Default voice (high quality American female)
# Full list: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
DEFAULT_VOICE = "af_heart"

# Default chunking settings (can be overridden via config)
DEFAULT_SHORT_TEXT_THRESHOLD = 200  # chars; below this, skip chunking
DEFAULT_TARGET_CHUNK_SIZE = 350     # chars; target size for sentence grouping
DEFAULT_MAX_CHUNK_SIZE = 500        # chars; hard limit before forcing chunk break

# Minimum sentence length - shorter segments get merged with previous
MIN_SENTENCE_LENGTH = 15


def segment_sentences(text: str) -> list[str]:
    """
    Segment text into sentences using pysbd.

    Handles abbreviations, decimals, and common edge cases better than regex.
    Very short segments are merged back into the previous sentence.

    Args:
        text: Text to segment

    Returns:
        List of sentences
    """
    try:
        import pysbd
    except ImportError:
        # Fallback to simple regex if pysbd not available
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    seg = pysbd.Segmenter(language="en", clean=False)
    raw_sentences = seg.segment(text)

    # Merge very short segments with previous sentence
    merged = []
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if merged and len(sentence) < MIN_SENTENCE_LENGTH:
            # Merge with previous
            merged[-1] = merged[-1] + " " + sentence
        else:
            merged.append(sentence)

    return merged


def chunk_sentences(
    sentences: list[str],
    target_size: int = DEFAULT_TARGET_CHUNK_SIZE,
    max_size: int = DEFAULT_MAX_CHUNK_SIZE,
) -> list[str]:
    """
    Group sentences into chunks targeting a character budget.

    This allows the TTS model to plan prosody across related sentences
    while keeping chunks small enough for good quality.

    Args:
        sentences: List of sentences to group
        target_size: Target chunk size in characters (~350 = 2-3 sentences)
        max_size: Maximum chunk size before forcing a break

    Returns:
        List of text chunks (each may contain multiple sentences)
    """
    if not sentences:
        return []

    chunks = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If adding this sentence would exceed max, flush current chunk
        if current and current_len + sentence_len + 1 > max_size:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = sentence_len
        # If we've reached target and sentence is substantial, start new chunk
        elif current and current_len >= target_size and sentence_len > MIN_SENTENCE_LENGTH:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = sentence_len
        else:
            current.append(sentence)
            current_len += sentence_len + (1 if current_len > 0 else 0)  # +1 for space

    if current:
        chunks.append(" ".join(current))

    return chunks


def strip_markdown_for_speech(text: str) -> str:
    """
    Convert markdown to plain text suitable for TTS.

    Strips formatting while preserving readable content.
    """
    # Remove mode injection tags [MODE: xyz] entirely
    text = re.sub(r"\[MODE:\s*[^\]]+\]", "", text)

    # Remove code blocks entirely (they don't speak well)
    text = re.sub(r"```[\s\S]*?```", " (code block) ", text)

    # Handle LaTeX display math $$...$$ - say "equation" for complex math
    text = re.sub(r"\$\$[\s\S]*?\$\$", " (equation) ", text)

    # Handle LaTeX inline math $...$ - extract content without dollar signs
    # For simple cases like $x$ just say "x", for complex say the content
    text = re.sub(r"\$([^$]+)\$", r"\1", text)

    # Clean up common LaTeX commands (after removing $ delimiters)
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)  # \command{content} -> content
    text = re.sub(r"\\[a-zA-Z]+", "", text)  # Remove remaining \commands
    text = re.sub(r"[\\{}^_]", " ", text)  # Remove LaTeX special chars

    # Handle Lean4 syntax - common Unicode math symbols
    lean_replacements = [
        (r"∀", "for all"),
        (r"∃", "there exists"),
        (r"→", "implies"),
        (r"←", "from"),
        (r"↔", "if and only if"),
        (r"λ", "lambda"),
        (r"Λ", "lambda"),
        (r"∧", "and"),
        (r"∨", "or"),
        (r"¬", "not"),
        (r"≠", "not equal to"),
        (r"≤", "less than or equal to"),
        (r"≥", "greater than or equal to"),
        (r"∈", "in"),
        (r"∉", "not in"),
        (r"⊆", "subset of"),
        (r"⊂", "proper subset of"),
        (r"∪", "union"),
        (r"∩", "intersection"),
        (r"∅", "empty set"),
        (r"⟨", ""),  # angle brackets - just remove
        (r"⟩", ""),
        (r"⊢", "proves"),
        (r"⊨", "models"),
        (r"≡", "equivalent to"),
        (r"∘", "composed with"),
        (r"×", "times"),
        (r"α", "alpha"),
        (r"β", "beta"),
        (r"γ", "gamma"),
        (r"δ", "delta"),
        (r"ε", "epsilon"),
        (r"ζ", "zeta"),
        (r"η", "eta"),
        (r"θ", "theta"),
        (r"ι", "iota"),
        (r"κ", "kappa"),
        (r"μ", "mu"),
        (r"ν", "nu"),
        (r"ξ", "xi"),
        (r"π", "pi"),
        (r"ρ", "rho"),
        (r"σ", "sigma"),
        (r"τ", "tau"),
        (r"υ", "upsilon"),
        (r"φ", "phi"),
        (r"χ", "chi"),
        (r"ψ", "psi"),
        (r"ω", "omega"),
    ]
    for symbol, replacement in lean_replacements:
        text = text.replace(symbol, f" {replacement} ")

    # Remove inline code but keep content
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Convert links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove images ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # Remove headers markers but keep text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove bold/italic markers (handle ** before *)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"__([^_]+)__", r"\1", text)      # __bold__
    text = re.sub(r"\*([^*]+)\*", r"\1", text)      # *italic*
    text = re.sub(r"_([^_]+)_", r"\1", text)        # _italic_

    # Remove strikethrough
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

    # Convert bullet points to natural pauses
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

    # Convert numbered lists
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove blockquote markers
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Collapse multiple newlines to single
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces
    text = re.sub(r"  +", " ", text)

    return text.strip()


class KokoroTTS:
    """High-quality local TTS using Kokoro."""

    SAMPLE_RATE = 24000

    def __init__(self, voice: str = DEFAULT_VOICE, lang_code: str = "a", speed: float = 1.0):
        """
        Initialize Kokoro TTS.

        Args:
            voice: Voice ID (e.g., "af_heart", "af_bella", "am_michael")
            lang_code: Language code ('a'=American, 'b'=British, etc.)
            speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        _ensure_tts_deps()
        self.voice = voice
        self.lang_code = lang_code
        self.speed = speed
        self._pipeline = None
        self._speaking = False
        self._stop_requested = False
        self._lock = threading.Lock()

    @property
    def pipeline(self):
        """Lazy-load the Kokoro pipeline."""
        if self._pipeline is None:
            from kokoro import KPipeline

            self._pipeline = KPipeline(
                lang_code=self.lang_code,
                repo_id="hexgrad/Kokoro-82M",
            )
        return self._pipeline

    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._speaking

    def speak(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """
        Speak text with streaming audio output.

        Args:
            text: Text to speak
            on_start: Callback when speech starts
            on_done: Callback when speech ends
        """
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
            self._stop_requested = False

        if on_start:
            on_start()

        stream = None
        try:
            for _, _, audio in self.pipeline(text, voice=self.voice, speed=self.speed):
                if self._stop_requested:
                    break

                # Convert PyTorch tensor to numpy
                audio_np = audio.cpu().numpy()

                # Open stream on first chunk
                if stream is None:
                    stream = sd.OutputStream(
                        samplerate=self.SAMPLE_RATE,
                        channels=1,
                        dtype="float32",
                    )
                    stream.start()

                stream.write(audio_np)

            if stream is not None:
                stream.stop()
                stream.close()
        finally:
            with self._lock:
                self._speaking = False
                self._stop_requested = False

            if on_done:
                on_done()

    def stop(self) -> None:
        """Stop speaking immediately."""
        self._stop_requested = True

    def speak_queued(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
        target_chunk_size: int = DEFAULT_TARGET_CHUNK_SIZE,
        max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    ) -> None:
        """
        Speak text using chunked synthesis with audio buffering.

        Text is segmented into sentences, then grouped into chunks targeting
        a character budget. Uses a producer-consumer pattern where chunks are
        synthesized ahead of playback, yielding better prosody while avoiding gaps.

        Args:
            text: Text to speak (will be segmented and chunked)
            on_start: Callback when speech starts
            on_done: Callback when speech ends
            target_chunk_size: Target chunk size in chars (~350 = 2-3 sentences)
            max_chunk_size: Maximum chunk size before forcing break
        """
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
            self._stop_requested = False

        sentences = segment_sentences(text)
        chunks = chunk_sentences(sentences, target_chunk_size, max_chunk_size)
        if not chunks:
            with self._lock:
                self._speaking = False
            if on_done:
                on_done()
            return

        audio_queue: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=3)
        producer_done = threading.Event()

        def produce():
            """Synthesize chunks and push audio to queue."""
            try:
                for chunk in chunks:
                    if self._stop_requested:
                        break
                    for _, _, audio in self.pipeline(chunk, voice=self.voice, speed=self.speed):
                        if self._stop_requested:
                            break
                        audio_queue.put(audio.cpu().numpy())
            finally:
                audio_queue.put(None)  # Sentinel to signal completion
                producer_done.set()

        def consume():
            """Pull audio chunks from queue and play continuously."""
            stream = None
            started = False
            try:
                while True:
                    try:
                        # Use timeout to allow checking stop flag
                        chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        if self._stop_requested or producer_done.is_set():
                            # Check one more time for remaining items
                            try:
                                chunk = audio_queue.get_nowait()
                            except queue.Empty:
                                break
                        continue

                    if chunk is None or self._stop_requested:
                        break

                    # Open stream on first chunk
                    if stream is None:
                        stream = sd.OutputStream(
                            samplerate=self.SAMPLE_RATE,
                            channels=1,
                            dtype="float32",
                        )
                        stream.start()
                        started = True
                        if on_start:
                            on_start()

                    stream.write(chunk)

            finally:
                if stream is not None:
                    stream.stop()
                    stream.close()
                # If we never started, still call on_start for consistency
                if not started and on_start:
                    on_start()

        producer = threading.Thread(target=produce, daemon=True)
        consumer = threading.Thread(target=consume, daemon=True)

        producer.start()
        consumer.start()

        producer.join()
        consumer.join()

        with self._lock:
            self._speaking = False
            self._stop_requested = False

        if on_done:
            on_done()


# Global speaker instance
_speaker: KokoroTTS | None = None


def get_speaker(voice: str = DEFAULT_VOICE, speed: float = 1.0) -> KokoroTTS:
    """
    Get or create the global speaker instance.

    Args:
        voice: Kokoro voice ID
        speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)

    Returns:
        KokoroTTS instance
    """
    global _speaker

    if _speaker is None or _speaker.voice != voice or _speaker.speed != speed:
        _speaker = KokoroTTS(voice=voice, speed=speed)

    return _speaker


def speak(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    on_start: Callable[[], None] | None = None,
    on_done: Callable[[], None] | None = None,
    strip_markdown: bool = True,
    short_text_threshold: int = DEFAULT_SHORT_TEXT_THRESHOLD,
    target_chunk_size: int = DEFAULT_TARGET_CHUNK_SIZE,
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
) -> None:
    """
    Speak text using Kokoro TTS.

    Automatically uses chunked synthesis with audio buffering for longer text
    to improve prosody quality, while using simple pass-through for short text
    to minimize overhead.

    Args:
        text: Text to speak
        voice: Kokoro voice ID (e.g., "af_heart", "af_bella")
        speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
        on_start: Callback when speech starts
        on_done: Callback when speech ends
        strip_markdown: Strip markdown formatting for natural speech
        short_text_threshold: Texts shorter than this use simple pass-through
        target_chunk_size: Target chunk size in chars for sentence grouping
        max_chunk_size: Maximum chunk size before forcing break
    """
    if strip_markdown:
        text = strip_markdown_for_speech(text)

    speaker = get_speaker(voice=voice, speed=speed)

    # Use queued chunked synthesis for longer text
    if len(text) > short_text_threshold:
        speaker.speak_queued(
            text,
            on_start=on_start,
            on_done=on_done,
            target_chunk_size=target_chunk_size,
            max_chunk_size=max_chunk_size,
        )
    else:
        speaker.speak(text, on_start=on_start, on_done=on_done)


def stop_speaking() -> None:
    """Stop any active speech."""
    global _speaker
    if _speaker is not None:
        _speaker.stop()


def is_speaking() -> bool:
    """Check if currently speaking."""
    global _speaker
    return _speaker is not None and _speaker.is_speaking
