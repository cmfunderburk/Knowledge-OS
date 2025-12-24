"""Shared TTS utilities for text processing and chunking."""

import re

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
