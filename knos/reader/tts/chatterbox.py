"""Chatterbox TTS backend implementation.

ResembleAI's Chatterbox - high quality zero-shot TTS.
https://github.com/resemble-ai/chatterbox
"""

import threading
import warnings
from typing import Callable

from knos.reader.tts.base import TTSBackend
from knos.reader.tts.utils import (
    segment_sentences,
    chunk_sentences,
)

# Suppress warnings from ML libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Chatterbox-specific chunking settings (smaller than Kokoro to avoid hallucination)
DEFAULT_TARGET_CHUNK_SIZE = 150  # chars; ~1-2 sentences
DEFAULT_MAX_CHUNK_SIZE = 250     # chars; hard limit

# Lazy imports for optional dependencies
np = None
sd = None


def _ensure_deps():
    """Import Chatterbox dependencies, raising ImportError if not available."""
    global np, sd
    if np is None:
        try:
            import numpy
            import sounddevice
            np = numpy
            sd = sounddevice
        except ImportError:
            raise ImportError(
                "Chatterbox TTS requires optional dependencies. "
                "Install with: uv sync --extra voice"
            )


def is_chatterbox_available() -> bool:
    """Check if Chatterbox dependencies are installed."""
    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        import chatterbox  # noqa: F401
        return True
    except ImportError:
        return False


class ChatterboxBackend(TTSBackend):
    """High-quality zero-shot TTS using ResembleAI Chatterbox.

    Supports both standard and turbo models:
    - standard: 500M params, more control (exaggeration, cfg_weight)
    - turbo: 350M params, ~2x faster, paralinguistic tags support
    """

    def __init__(
        self,
        model_type: str = "standard",
        exaggeration: float = 0.3,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
        voice_sample: str | None = None,
        device: str | None = None,
    ):
        """
        Initialize Chatterbox TTS backend.

        Args:
            model_type: "standard" (500M, more control) or "turbo" (350M, faster)
            exaggeration: Expressiveness control (0.0-1.0, standard only)
            cfg_weight: Speaker adherence/pacing (0.0-1.0, standard only)
            temperature: Randomness/variation (0.0-1.0, both models)
            voice_sample: Path to WAV file for voice cloning (optional)
            device: Device to run on ("cuda", "cpu", or None for auto-detect)

        Note: Turbo model only uses temperature; exaggeration and cfg_weight are ignored.
        """
        _ensure_deps()
        self.model_type = model_type
        self.exaggeration = exaggeration
        self.cfg_weight = cfg_weight
        self.temperature = temperature
        self.voice_sample = voice_sample
        self._device = device
        self._model = None
        self._speaking = False
        self._stop_requested = False
        self._lock = threading.Lock()
        self._voice_prepared = False

    @property
    def device(self) -> str:
        """Get device, auto-detecting if not specified."""
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    @property
    def model(self):
        """Lazy-load the Chatterbox model."""
        if self._model is None:
            if self.model_type == "turbo":
                from chatterbox.tts_turbo import ChatterboxTurboTTS
                self._model = ChatterboxTurboTTS.from_pretrained(device=self.device)
            else:
                from chatterbox.tts import ChatterboxTTS
                self._model = ChatterboxTTS.from_pretrained(device=self.device)
        return self._model

    @property
    def SAMPLE_RATE(self) -> int:
        """Get sample rate from model."""
        return self.model.sr

    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._speaking

    def _prepare_voice(self) -> None:
        """Prepare voice conditionals from sample if specified."""
        if self._voice_prepared:
            return
        if self.voice_sample:
            # Prepare conditionals from voice sample (only needs to be done once)
            self.model.prepare_conditionals(
                self.voice_sample,
                exaggeration=self.exaggeration if self.model_type != "turbo" else 0.0,
            )
        self._voice_prepared = True

    def _generate_audio(self, text: str) -> "np.ndarray":
        """Generate audio for text, returning numpy array."""
        # Prepare voice from sample if configured (lazy, once per session)
        self._prepare_voice()

        # Generate audio - voice conditionals already prepared
        # Turbo only supports temperature; standard supports all params
        if self.model_type == "turbo":
            wav = self.model.generate(text, temperature=self.temperature)
        else:
            wav = self.model.generate(
                text,
                exaggeration=self.exaggeration,
                cfg_weight=self.cfg_weight,
                temperature=self.temperature,
            )
        # Convert PyTorch tensor to numpy
        # Chatterbox returns [1, samples] or [samples] tensor
        audio_np = wav.cpu().numpy()
        if audio_np.ndim == 2:
            audio_np = audio_np.squeeze(0)
        # Ensure float32 for sounddevice
        return audio_np.astype(np.float32)

    def speak(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """
        Speak text (generates full audio then plays).

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

        try:
            # Generate full audio (Chatterbox doesn't support streaming)
            audio_np = self._generate_audio(text)

            if self._stop_requested:
                return

            if on_start:
                on_start()

            # Play audio
            self._play_audio(audio_np)

        finally:
            with self._lock:
                self._speaking = False
                self._stop_requested = False

            if on_done:
                on_done()

    def _play_audio(self, audio: "np.ndarray") -> None:
        """Play audio array, checking for stop requests."""
        # Play in chunks to allow stopping
        chunk_size = self.SAMPLE_RATE // 4  # 250ms chunks
        stream = sd.OutputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        stream.start()

        try:
            for i in range(0, len(audio), chunk_size):
                if self._stop_requested:
                    break
                chunk = audio[i:i + chunk_size]
                stream.write(chunk)
        finally:
            stream.stop()
            stream.close()

    def speak_chunked(
        self,
        text: str,
        on_start: Callable[[], None] | None = None,
        on_done: Callable[[], None] | None = None,
        target_chunk_size: int = DEFAULT_TARGET_CHUNK_SIZE,
        max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    ) -> None:
        """
        Speak text using chunked synthesis to avoid hallucination on long text.

        Pre-generates all chunks first, then plays them back-to-back for
        gapless playback. This avoids the hallucination that occurs when
        Chatterbox is given text that's too long.

        Args:
            text: Text to speak (will be segmented and chunked)
            on_start: Callback when speech starts
            on_done: Callback when speech ends
            target_chunk_size: Target chunk size in characters
            max_chunk_size: Maximum chunk size before forcing break
        """
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
            self._stop_requested = False

        # Segment and chunk the text
        sentences = segment_sentences(text)
        chunks = chunk_sentences(sentences, target_chunk_size, max_chunk_size)

        if not chunks:
            with self._lock:
                self._speaking = False
            if on_done:
                on_done()
            return

        try:
            # Phase 1: Pre-generate all audio chunks
            audio_chunks: list[np.ndarray] = []
            for chunk in chunks:
                if self._stop_requested:
                    break
                audio_np = self._generate_audio(chunk)
                audio_chunks.append(audio_np)

            if self._stop_requested or not audio_chunks:
                return

            # Phase 2: Play all chunks back-to-back
            if on_start:
                on_start()

            for audio in audio_chunks:
                if self._stop_requested:
                    break
                self._play_audio(audio)

        finally:
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
        if self._model is not None:
            import gc
            import torch
            # Move submodules to CPU first to free CUDA memory
            # Chatterbox has t3, s3gen, ve submodules
            for attr in ["t3", "s3gen", "ve"]:
                submodule = getattr(self._model, attr, None)
                if submodule is not None and hasattr(submodule, "to"):
                    try:
                        submodule.to("cpu")
                    except Exception:
                        pass
            del self._model
            self._model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
