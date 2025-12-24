"""Kokoro TTS backend implementation."""

import queue
import threading
import warnings
from typing import Callable

from knos.reader.tts.base import TTSBackend
from knos.reader.tts.utils import (
    segment_sentences,
    chunk_sentences,
    DEFAULT_TARGET_CHUNK_SIZE,
    DEFAULT_MAX_CHUNK_SIZE,
)

# Suppress warnings from ML libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Default voice (high quality American female)
# Full list: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
DEFAULT_VOICE = "af_heart"

# Lazy imports for optional dependencies
np = None
sd = None


def _ensure_deps():
    """Import Kokoro dependencies, raising ImportError if not available."""
    global np, sd
    if np is None:
        try:
            import numpy
            import sounddevice
            np = numpy
            sd = sounddevice
        except ImportError:
            raise ImportError(
                "Kokoro TTS requires optional dependencies. "
                "Install with: uv sync --extra voice"
            )


def is_kokoro_available() -> bool:
    """Check if Kokoro dependencies are installed."""
    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        import kokoro  # noqa: F401
        return True
    except ImportError:
        return False


class KokoroBackend(TTSBackend):
    """High-quality local TTS using Kokoro."""

    SAMPLE_RATE = 24000

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        lang_code: str = "a",
        speed: float = 1.0,
    ):
        """
        Initialize Kokoro TTS backend.

        Args:
            voice: Voice ID (e.g., "af_heart", "af_bella", "am_michael")
            lang_code: Language code ('a'=American, 'b'=British, etc.)
            speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        _ensure_deps()
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

    def speak_chunked(
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

    def stop(self) -> None:
        """Stop speaking immediately."""
        self._stop_requested = True

    def unload(self) -> None:
        """Unload model from VRAM to free memory."""
        if self._pipeline is not None:
            import gc
            import torch
            del self._pipeline
            self._pipeline = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
