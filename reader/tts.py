"""Text-to-speech module using Kokoro for high-quality local neural TTS."""
import os
import re
import threading
import warnings
from typing import Callable

import numpy as np
import sounddevice as sd

# Suppress warnings from ML libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

_cuda_available: bool | None = None


def _check_cuda_available() -> bool:
    """Check if CUDA is available for PyTorch."""
    global _cuda_available
    if _cuda_available is not None:
        return _cuda_available

    try:
        import torch
        _cuda_available = torch.cuda.is_available()
    except ImportError:
        _cuda_available = False

    return _cuda_available


def _preload_nvidia_libraries():
    """Preload NVIDIA libraries so PyTorch can find them."""
    if not _check_cuda_available():
        return

    import ctypes
    import importlib.util

    libs_to_load = [
        ("nvidia.nccl.lib", "libnccl.so.2"),
        ("nvidia.cublas.lib", "libcublas.so.12"),
        ("nvidia.cudnn.lib", "libcudnn.so.9"),
    ]

    for module_name, lib_name in libs_to_load:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.submodule_search_locations:
                lib_path = os.path.join(spec.submodule_search_locations[0], lib_name)
                if os.path.exists(lib_path):
                    ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            pass


_preload_nvidia_libraries()

# Default voice (high quality American female)
# Full list: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
DEFAULT_VOICE = "af_heart"


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
) -> None:
    """
    Speak text using Kokoro TTS.

    Args:
        text: Text to speak
        voice: Kokoro voice ID (e.g., "af_heart", "af_bella")
        speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
        on_start: Callback when speech starts
        on_done: Callback when speech ends
        strip_markdown: Strip markdown formatting for natural speech
    """
    if strip_markdown:
        text = strip_markdown_for_speech(text)
    speaker = get_speaker(voice=voice, speed=speed)
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
