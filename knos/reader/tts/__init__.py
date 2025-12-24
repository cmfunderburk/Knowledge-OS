"""Text-to-speech module with pluggable backends.

Currently supports:
- kokoro: Fast, lightweight local TTS (default)
- chatterbox: High-quality zero-shot TTS from ResembleAI

Configure in config/reader.yaml:

    tts:
      backend: "kokoro"  # or "chatterbox"
      kokoro:
        voice: "af_heart"
      chatterbox:
        exaggeration: 0.5
        cfg_weight: 0.5

Requires optional voice dependencies: uv sync --extra voice
"""

from typing import Callable

from knos.reader.tts.base import TTSBackend
from knos.reader.tts.utils import (
    strip_markdown_for_speech,
    segment_sentences,
    chunk_sentences,
    DEFAULT_SHORT_TEXT_THRESHOLD,
    DEFAULT_TARGET_CHUNK_SIZE,
    DEFAULT_MAX_CHUNK_SIZE,
)

# Preload NVIDIA libraries (must happen before importing torch/kokoro)
from knos.reader.cuda_utils import is_cuda_available  # noqa: F401

# Global backend instance
_backend: TTSBackend | None = None
_backend_config: dict | None = None


def is_tts_available() -> bool:
    """Check if any TTS backend is available."""
    try:
        from knos.reader.tts.kokoro import is_kokoro_available
        if is_kokoro_available():
            return True
    except ImportError:
        pass

    try:
        from knos.reader.tts.chatterbox import is_chatterbox_available
        if is_chatterbox_available():
            return True
    except ImportError:
        pass

    return False


def get_backend(config: dict | None = None) -> TTSBackend:
    """
    Factory function to create the configured TTS backend.

    Args:
        config: Optional config dict. If None, loads from reader.yaml

    Returns:
        Configured TTSBackend instance

    Raises:
        ValueError: If unknown backend specified
        ImportError: If backend dependencies not installed
    """
    if config is None:
        from knos.reader.config import load_config
        config = load_config()

    tts_config = config.get("tts", {})
    backend_name = tts_config.get("backend", "kokoro")
    speed = tts_config.get("speed", 1.0)

    if backend_name == "kokoro":
        from knos.reader.tts.kokoro import KokoroBackend

        # Support both nested and flat config for backward compatibility
        kokoro_config = tts_config.get("kokoro", {})
        voice = kokoro_config.get("voice") or tts_config.get("voice", "af_heart")

        return KokoroBackend(
            voice=voice,
            speed=speed,
        )

    elif backend_name == "chatterbox":
        from knos.reader.tts.chatterbox import ChatterboxBackend

        chatterbox_config = tts_config.get("chatterbox", {})
        model_type = chatterbox_config.get("model", "standard")
        exaggeration = chatterbox_config.get("exaggeration", 0.3)
        cfg_weight = chatterbox_config.get("cfg_weight", 0.5)
        temperature = chatterbox_config.get("temperature", 0.8)
        voice_sample = chatterbox_config.get("voice_sample")  # None = default voice
        device = chatterbox_config.get("device")  # None = auto-detect

        return ChatterboxBackend(
            model_type=model_type,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
            voice_sample=voice_sample,
            device=device,
        )

    else:
        raise ValueError(
            f"Unknown TTS backend: {backend_name}. "
            "Supported backends: 'kokoro', 'chatterbox'"
        )


def _get_or_create_backend(config: dict | None = None) -> TTSBackend:
    """Get existing backend or create new one if config changed."""
    global _backend, _backend_config

    # Load config if not provided
    if config is None:
        from knos.reader.config import load_config
        config = load_config()

    tts_config = config.get("tts", {})

    # Check if we need to recreate the backend
    if _backend is None or _backend_config != tts_config:
        if _backend is not None:
            _backend.unload()  # Free VRAM before loading new backend
        _backend = get_backend(config)
        _backend_config = tts_config.copy()

    return _backend


def speak(
    text: str,
    on_start: Callable[[], None] | None = None,
    on_done: Callable[[], None] | None = None,
    strip_markdown: bool = True,
    short_text_threshold: int | None = None,
    target_chunk_size: int | None = None,
    max_chunk_size: int | None = None,
    config: dict | None = None,
    **kwargs,  # Accept but ignore legacy kwargs like voice, speed
) -> None:
    """
    Speak text using the configured TTS backend.

    Automatically uses chunked synthesis for longer text to improve
    prosody quality, while using simple pass-through for short text.

    Args:
        text: Text to speak
        on_start: Callback when speech starts
        on_done: Callback when speech ends
        strip_markdown: Strip markdown formatting for natural speech
        short_text_threshold: Texts shorter than this use simple synthesis
        target_chunk_size: Target chunk size for sentence grouping
        max_chunk_size: Maximum chunk size before forcing break
        config: Optional config dict (uses reader.yaml if not provided)
    """
    if strip_markdown:
        text = strip_markdown_for_speech(text)

    if not text.strip():
        if on_start:
            on_start()
        if on_done:
            on_done()
        return

    backend = _get_or_create_backend(config)

    # Get chunking settings from config or use defaults
    if config is None:
        from knos.reader.config import load_config
        config = load_config()

    tts_config = config.get("tts", {})
    backend_name = tts_config.get("backend", "kokoro")

    # Use backend-specific defaults for chunking
    # Chatterbox needs smaller chunks to avoid hallucination
    if backend_name == "chatterbox":
        default_threshold = 100  # Lower threshold - chunk more aggressively
        default_target = 150     # Smaller chunks (~1-2 sentences)
        default_max = 250
    else:
        default_threshold = DEFAULT_SHORT_TEXT_THRESHOLD
        default_target = DEFAULT_TARGET_CHUNK_SIZE
        default_max = DEFAULT_MAX_CHUNK_SIZE

    threshold = short_text_threshold or tts_config.get(
        "short_text_threshold", default_threshold
    )
    target = target_chunk_size or tts_config.get(
        "target_chunk_size", default_target
    )
    max_size = max_chunk_size or tts_config.get(
        "max_chunk_size", default_max
    )

    # Use chunked synthesis for longer text
    if len(text) > threshold:
        backend.speak_chunked(
            text,
            on_start=on_start,
            on_done=on_done,
            target_chunk_size=target,
            max_chunk_size=max_size,
        )
    else:
        backend.speak(text, on_start=on_start, on_done=on_done)


def stop_speaking() -> None:
    """Stop any active speech."""
    global _backend
    if _backend is not None:
        _backend.stop()


def is_speaking() -> bool:
    """Check if currently speaking."""
    global _backend
    return _backend is not None and _backend.is_speaking


def unload_backend() -> None:
    """Unload TTS model from VRAM to free memory."""
    global _backend, _backend_config
    if _backend is not None:
        _backend.unload()
        _backend = None
        _backend_config = None


# Re-export for convenience
__all__ = [
    "TTSBackend",
    "get_backend",
    "speak",
    "stop_speaking",
    "is_speaking",
    "unload_backend",
    "is_tts_available",
    "strip_markdown_for_speech",
    "segment_sentences",
    "chunk_sentences",
]
