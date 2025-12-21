"""Voice input module using faster-whisper for local transcription.

Requires optional voice dependencies: uv sync --extra voice
"""
import os
import queue
import threading
from typing import Callable

# Check if voice dependencies are available
_voice_available: bool | None = None


def is_voice_available() -> bool:
    """Check if voice input dependencies are installed."""
    global _voice_available
    if _voice_available is not None:
        return _voice_available

    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        import faster_whisper  # noqa: F401
        _voice_available = True
    except ImportError:
        _voice_available = False

    return _voice_available


_cuda_available: bool | None = None


def _check_cuda_available() -> bool:
    """Check if CUDA is available for faster-whisper."""
    global _cuda_available
    if _cuda_available is not None:
        return _cuda_available

    try:
        import torch
        _cuda_available = torch.cuda.is_available()
    except ImportError:
        _cuda_available = False

    return _cuda_available


def _preload_cuda_libraries():
    """Preload NVIDIA libraries so ctranslate2/faster-whisper can find them."""
    if not _check_cuda_available():
        return

    import ctypes
    import importlib.util

    libs_to_load = [
        ("nvidia.cublas.lib", "libcublas.so.12"),
        ("nvidia.cublas.lib", "libcublasLt.so.12"),
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


_preload_cuda_libraries()

# Lazy imports for optional dependencies
np = None
sd = None


def _ensure_voice_deps():
    """Import voice dependencies, raising ImportError if not available."""
    global np, sd
    if np is None:
        if not is_voice_available():
            raise ImportError(
                "Voice input requires optional dependencies. "
                "Install with: uv sync --extra voice"
            )
        import numpy
        import sounddevice
        np = numpy
        sd = sounddevice


class WhisperTranscriber:
    """Local Whisper transcription using faster-whisper with GPU/CPU support."""

    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        device: str | None = None,
        compute_type: str | None = None,
    ):
        """
        Initialize the transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3)
            language: Language code for transcription
            device: "cuda" for GPU, "cpu" for CPU, or None for auto-detect
            compute_type: "float16" for GPU, "int8" for CPU, or None for auto
        """
        _ensure_voice_deps()
        self.model_size = model_size
        self.language = language

        # Auto-detect device and compute type
        if device is None:
            self.device = "cuda" if _check_cuda_available() else "cpu"
        else:
            self.device = device

        if compute_type is None:
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type

        self._model = None

    @property
    def model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize if needed
        if audio.max() > 1.0 or audio.min() < -1.0:
            audio = audio / max(abs(audio.max()), abs(audio.min()))

        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )

        # Concatenate all segments
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()


class VoiceRecorder:
    """Audio recorder with silence detection."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 60.0,
    ):
        """
        Initialize the recorder.

        Args:
            sample_rate: Audio sample rate
            channels: Number of audio channels (1 for mono)
            silence_threshold: RMS threshold below which audio is considered silence
            silence_duration: Seconds of silence before stopping
            max_duration: Maximum recording duration in seconds
        """
        _ensure_voice_deps()
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration

        self._recording = False
        self._audio_queue: queue.Queue = queue.Queue()

    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            print(f"Audio status: {status}")
        self._audio_queue.put(indata.copy())

    def record_until_silence(
        self,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> np.ndarray:
        """
        Record audio until silence is detected.

        Args:
            on_start: Callback when recording starts
            on_stop: Callback when recording stops

        Returns:
            Audio data as numpy array
        """
        self._recording = True
        audio_chunks = []
        silence_samples = 0
        silence_samples_needed = int(self.silence_duration * self.sample_rate)
        max_samples = int(self.max_duration * self.sample_rate)
        total_samples = 0

        if on_start:
            on_start()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=1024,
            ):
                while self._recording:
                    try:
                        chunk = self._audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    audio_chunks.append(chunk)
                    total_samples += len(chunk)

                    # Check for silence
                    rms = np.sqrt(np.mean(chunk**2))
                    if rms < self.silence_threshold:
                        silence_samples += len(chunk)
                    else:
                        silence_samples = 0

                    # Stop conditions
                    if silence_samples >= silence_samples_needed:
                        break
                    if total_samples >= max_samples:
                        break

        finally:
            self._recording = False
            if on_stop:
                on_stop()

        if not audio_chunks:
            return np.array([], dtype=np.float32)

        # Concatenate all chunks
        audio = np.concatenate(audio_chunks, axis=0)

        # Flatten to mono if needed
        if audio.ndim > 1:
            audio = audio.flatten()

        return audio

    def stop(self):
        """Stop recording early."""
        self._recording = False


# Global instances for reuse
_transcriber: WhisperTranscriber | None = None
_recorder: VoiceRecorder | None = None


def get_transcriber(
    model_size: str = "base",
    language: str = "en",
) -> WhisperTranscriber:
    """Get or create the global transcriber instance."""
    global _transcriber
    if _transcriber is None or _transcriber.model_size != model_size:
        _transcriber = WhisperTranscriber(model_size=model_size, language=language)
    return _transcriber


def get_recorder(
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5,
) -> VoiceRecorder:
    """Get or create the global recorder instance."""
    global _recorder
    if _recorder is None:
        _recorder = VoiceRecorder(
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
        )
    return _recorder


def record_and_transcribe(
    model_size: str = "base",
    language: str = "en",
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5,
    on_recording_start: Callable[[], None] | None = None,
    on_recording_stop: Callable[[], None] | None = None,
    on_transcribing: Callable[[], None] | None = None,
) -> str:
    """
    Convenience function to record and transcribe in one call.

    Args:
        model_size: Whisper model size
        language: Language code
        silence_threshold: RMS threshold for silence detection
        silence_duration: Seconds of silence before stopping
        on_recording_start: Callback when recording starts
        on_recording_stop: Callback when recording stops
        on_transcribing: Callback when transcription starts

    Returns:
        Transcribed text
    """
    recorder = get_recorder(silence_threshold, silence_duration)
    transcriber = get_transcriber(model_size, language)

    # Record
    audio = recorder.record_until_silence(
        on_start=on_recording_start,
        on_stop=on_recording_stop,
    )

    if len(audio) == 0:
        return ""

    # Transcribe
    if on_transcribing:
        on_transcribing()

    return transcriber.transcribe(audio)


def stop_recording() -> None:
    """Stop any active recording."""
    global _recorder
    if _recorder is not None:
        _recorder.stop()
