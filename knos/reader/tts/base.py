"""Abstract base class for TTS backends."""

from abc import ABC, abstractmethod
from typing import Callable


class TTSBackend(ABC):
    """Abstract base class for TTS backends."""

    SAMPLE_RATE: int = 24000  # Default sample rate, backends can override

    @property
    @abstractmethod
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        pass

    @abstractmethod
    def speak(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """
        Speak text (blocking until complete or stopped).

        Args:
            text: Text to speak
            on_start: Callback when speech starts
            on_done: Callback when speech ends (or is stopped)
        """
        pass

    @abstractmethod
    def speak_chunked(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
        target_chunk_size: int = 350,
        max_chunk_size: int = 500,
    ) -> None:
        """
        Speak text using chunked synthesis for better prosody on long text.

        Text is segmented into sentences, then grouped into chunks.
        Uses producer-consumer pattern for gapless playback.

        Args:
            text: Text to speak (will be segmented and chunked)
            on_start: Callback when speech starts
            on_done: Callback when speech ends
            target_chunk_size: Target chunk size in characters
            max_chunk_size: Maximum chunk size before forcing break
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop speaking immediately."""
        pass

    def unload(self) -> None:
        """Unload model from memory. Override in subclasses that load models."""
        pass
