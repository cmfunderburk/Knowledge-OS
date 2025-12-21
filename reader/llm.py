"""
LLM provider abstraction for the reader module.
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from reader.config import load_config


@dataclass
class ChatResponse:
    """Response from an LLM provider including token usage."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: list[dict], system: str | None = None) -> ChatResponse:
        """
        Send messages and get a response.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system: Optional system prompt

        Returns:
            ChatResponse with text and token counts
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider using the new google-genai SDK with context caching."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._cache_name: str | None = None

    def create_cache(
        self,
        system_prompt: str,
        chapter_content: str | None = None,
        chapter_pdf: bytes | None = None,
        ttl_seconds: int = 900,
    ) -> str | None:
        """
        Create a context cache with system prompt and chapter content.

        Args:
            system_prompt: System instruction for the dialogue mode.
            chapter_content: The chapter text for EPUBs (mutually exclusive with chapter_pdf)
            chapter_pdf: The chapter PDF bytes for PDFs (mutually exclusive with chapter_content)
            ttl_seconds: Cache TTL in seconds (default 15 minutes)

        Returns:
            Cache name for reference, or None if content too small

        Note:
            Gemini requires minimum ~2048 tokens for caching.
            For text: rough estimate 4 chars per token, so ~8K chars minimum.
            For PDFs: always cache (visual content is substantial).
        """
        # Skip caching for small text content (< ~2K tokens)
        if chapter_content and not chapter_pdf:
            total_content = system_prompt + chapter_content
            if len(total_content) < 8000:
                return None

        # Clear any existing cache first
        self.clear_cache()

        from google.genai import types

        # Build content part based on format
        if chapter_pdf:
            content_part = types.Part.from_bytes(data=chapter_pdf, mime_type="application/pdf")
        else:
            content_part = types.Part.from_text(text=f"<chapter>\n{chapter_content}\n</chapter>")

        cache = self.client.caches.create(
            model=self.model,
            config=types.CreateCachedContentConfig(
                system_instruction=system_prompt,
                contents=[
                    types.Content(
                        role="user",
                        parts=[content_part]
                    )
                ],
                ttl=f"{ttl_seconds}s",
            )
        )
        self._cache_name = cache.name
        return cache.name

    def clear_cache(self) -> None:
        """Delete the current cache if one exists."""
        if self._cache_name:
            try:
                self.client.caches.delete(self._cache_name)
            except Exception:
                pass  # Cache may have already expired
            self._cache_name = None

    def chat(self, messages: list[dict], system: str | None = None) -> ChatResponse:
        """Send messages to Gemini, using cache if available."""
        from google.genai import types

        # Convert messages to Gemini Content format
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # Build generation config
        # Note: system_instruction cannot be used with cached_content
        if self._cache_name:
            gen_config = types.GenerateContentConfig(
                cached_content=self._cache_name,
            )
        else:
            gen_config = types.GenerateContentConfig(
                system_instruction=system,
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=gen_config,
        )

        # Extract token counts from usage metadata
        input_tokens = 0
        output_tokens = 0
        cached_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            cached_tokens = getattr(response.usage_metadata, "cached_content_token_count", 0) or 0

        return ChatResponse(
            text=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )


def get_provider(config: dict[str, Any] | None = None) -> LLMProvider:
    """
    Factory function to create the configured LLM provider.

    Args:
        config: Optional config dict. If None, loads from config.yaml

    Returns:
        Configured LLMProvider instance
    """
    if config is None:
        config = load_config()

    llm_config = config.get("llm", {})
    provider_name = llm_config.get("provider", "gemini")

    if provider_name != "gemini":
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            "Only 'gemini' is currently supported (requires context caching)."
        )

    gemini_config = llm_config.get("gemini", {})
    api_key = gemini_config.get("api_key") or os.environ.get(
        gemini_config.get("api_key_env", "GOOGLE_API_KEY")
    )
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Set in config.yaml or GOOGLE_API_KEY env var"
        )
    model = gemini_config.get("model", "gemini-2.5-flash")
    return GeminiProvider(api_key=api_key, model=model)
