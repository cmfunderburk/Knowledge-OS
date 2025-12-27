"""Shared TTS utilities for text processing and chunking."""

import re

# LaTeX command to Unicode mappings
# Used for both display (TUI) and TTS preprocessing
LATEX_TO_UNICODE = {
    # Greek letters (lowercase)
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\varepsilon": "ε",
    r"\zeta": "ζ",
    r"\eta": "η",
    r"\theta": "θ",
    r"\iota": "ι",
    r"\kappa": "κ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\xi": "ξ",
    r"\pi": "π",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\upsilon": "υ",
    r"\phi": "φ",
    r"\varphi": "φ",
    r"\chi": "χ",
    r"\psi": "ψ",
    r"\omega": "ω",
    # Greek letters (uppercase)
    r"\Gamma": "Γ",
    r"\Delta": "Δ",
    r"\Theta": "Θ",
    r"\Lambda": "Λ",
    r"\Xi": "Ξ",
    r"\Pi": "Π",
    r"\Sigma": "Σ",
    r"\Phi": "Φ",
    r"\Psi": "Ψ",
    r"\Omega": "Ω",
    # Set theory
    r"\in": "∈",
    r"\notin": "∉",
    r"\subset": "⊂",
    r"\supset": "⊃",
    r"\subseteq": "⊆",
    r"\supseteq": "⊇",
    r"\cup": "∪",
    r"\cap": "∩",
    r"\emptyset": "∅",
    r"\varnothing": "∅",
    # Logic
    r"\forall": "∀",
    r"\exists": "∃",
    r"\nexists": "∄",
    r"\neg": "¬",
    r"\lnot": "¬",
    r"\land": "∧",
    r"\lor": "∨",
    r"\implies": "⇒",
    r"\Rightarrow": "⇒",
    r"\Leftarrow": "⇐",
    r"\Leftrightarrow": "⇔",
    r"\iff": "⇔",
    r"\to": "→",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\leftrightarrow": "↔",
    r"\mapsto": "↦",
    # Relations
    r"\le": "≤",
    r"\leq": "≤",
    r"\ge": "≥",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\ne": "≠",
    r"\equiv": "≡",
    r"\approx": "≈",
    r"\sim": "∼",
    r"\simeq": "≃",
    r"\propto": "∝",
    r"\prec": "≺",
    r"\succ": "≻",
    r"\preceq": "⪯",
    r"\succeq": "⪰",
    # Operators
    r"\times": "×",
    r"\cdot": "·",
    r"\circ": "∘",
    r"\pm": "±",
    r"\mp": "∓",
    r"\div": "÷",
    r"\ast": "∗",
    r"\star": "⋆",
    r"\oplus": "⊕",
    r"\otimes": "⊗",
    # Calculus / Analysis
    r"\infty": "∞",
    r"\partial": "∂",
    r"\nabla": "∇",
    r"\sum": "Σ",
    r"\prod": "Π",
    r"\int": "∫",
    r"\sqrt": "√",
    # Misc
    r"\prime": "′",
    r"\dots": "…",
    r"\cdots": "⋯",
    r"\ldots": "…",
    r"\vdots": "⋮",
    r"\angle": "∠",
    r"\triangle": "△",
    r"\square": "□",
    r"\langle": "⟨",
    r"\rangle": "⟩",
    r"\lceil": "⌈",
    r"\rceil": "⌉",
    r"\lfloor": "⌊",
    r"\rfloor": "⌋",
    r"\perp": "⊥",
    r"\parallel": "∥",
    r"\therefore": "∴",
    r"\because": "∵",
}


def latex_to_unicode(text: str) -> str:
    """
    Convert LaTeX math notation to Unicode for display.

    Handles:
    - Inline math: $c(A) \\subseteq A$ → c(A) ⊆ A
    - Display math: $$...$$ → (equation block)
    - Bare LaTeX commands in text

    Args:
        text: Text potentially containing LaTeX

    Returns:
        Text with LaTeX converted to Unicode
    """
    # Handle display math blocks - replace with placeholder
    text = re.sub(r"\$\$[\s\S]*?\$\$", " (equation) ", text)

    def convert_math(match: re.Match) -> str:
        """Convert content inside $...$ delimiters."""
        content = match.group(1)

        # Replace LaTeX commands with Unicode (longest first to avoid partial matches)
        for cmd, symbol in sorted(LATEX_TO_UNICODE.items(), key=lambda x: -len(x[0])):
            content = content.replace(cmd, symbol)

        # Clean up common LaTeX artifacts
        content = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", content)  # \cmd{x} → x
        content = re.sub(r"\\[a-zA-Z]+", "", content)  # remaining \commands
        content = re.sub(r"[{}]", "", content)  # braces
        content = re.sub(r"\^(\w)", r"^\1", content)  # keep simple superscripts
        content = re.sub(r"_(\w)", r"_\1", content)  # keep simple subscripts

        return content

    # Convert inline math $...$
    text = re.sub(r"\$([^$]+)\$", convert_math, text)

    # Also handle bare LaTeX commands outside of math mode
    for cmd, symbol in sorted(LATEX_TO_UNICODE.items(), key=lambda x: -len(x[0])):
        text = text.replace(cmd, symbol)

    return text


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
    # First convert any LaTeX to Unicode symbols
    text = latex_to_unicode(text)

    # Remove mode injection tags [MODE: xyz] entirely
    text = re.sub(r"\[MODE:\s*[^\]]+\]", "", text)

    # Remove code blocks entirely (they don't speak well)
    text = re.sub(r"```[\s\S]*?```", " (code block) ", text)

    # Clean up any remaining LaTeX artifacts
    text = re.sub(r"[\\{}^_]", " ", text)

    # Unicode math symbols to speech
    symbol_replacements = [
        # Logic and quantifiers
        ("∀", "for all"),
        ("∃", "there exists"),
        ("∄", "there does not exist"),
        ("→", "implies"),
        ("←", "from"),
        ("↔", "if and only if"),
        ("⇒", "implies"),
        ("⇐", "is implied by"),
        ("⇔", "if and only if"),
        ("↦", "maps to"),
        ("∧", "and"),
        ("∨", "or"),
        ("¬", "not"),
        # Relations
        ("≠", "not equal to"),
        ("≤", "less than or equal to"),
        ("≥", "greater than or equal to"),
        ("≈", "approximately"),
        ("≡", "equivalent to"),
        ("∼", "similar to"),
        ("≃", "approximately equal to"),
        ("∝", "proportional to"),
        ("≺", "precedes"),
        ("≻", "succeeds"),
        # Set theory
        ("∈", "in"),
        ("∉", "not in"),
        ("⊆", "subset of"),
        ("⊇", "superset of"),
        ("⊂", "proper subset of"),
        ("⊃", "proper superset of"),
        ("∪", "union"),
        ("∩", "intersection"),
        ("∅", "empty set"),
        # Operators
        ("×", "times"),
        ("·", "dot"),
        ("∘", "composed with"),
        ("±", "plus or minus"),
        ("∓", "minus or plus"),
        ("÷", "divided by"),
        ("⊕", "direct sum"),
        ("⊗", "tensor product"),
        # Calculus / Analysis
        ("∞", "infinity"),
        ("∂", "partial"),
        ("∇", "nabla"),
        ("∫", "integral"),
        ("√", "square root of"),
        ("Σ", "sum"),
        ("Π", "product"),
        # Brackets (remove)
        ("⟨", ""),
        ("⟩", ""),
        ("⌈", ""),
        ("⌉", ""),
        ("⌊", ""),
        ("⌋", ""),
        # Proof / Logic symbols
        ("⊢", "proves"),
        ("⊨", "models"),
        ("⊥", "contradiction"),
        ("∥", "parallel to"),
        ("∴", "therefore"),
        ("∵", "because"),
        # Primes
        ("′", " prime"),
        ("″", " double prime"),
        # Greek letters (lowercase)
        ("α", "alpha"),
        ("β", "beta"),
        ("γ", "gamma"),
        ("δ", "delta"),
        ("ε", "epsilon"),
        ("ζ", "zeta"),
        ("η", "eta"),
        ("θ", "theta"),
        ("ι", "iota"),
        ("κ", "kappa"),
        ("λ", "lambda"),
        ("μ", "mu"),
        ("µ", "mu"),  # micro sign variant
        ("ν", "nu"),
        ("ξ", "xi"),
        ("π", "pi"),
        ("ρ", "rho"),
        ("σ", "sigma"),
        ("τ", "tau"),
        ("υ", "upsilon"),
        ("φ", "phi"),
        ("ϕ", "phi"),  # phi variant
        ("χ", "chi"),
        ("ψ", "psi"),
        ("ω", "omega"),
        # Greek letters (uppercase)
        ("Γ", "Gamma"),
        ("Δ", "Delta"),
        ("Θ", "Theta"),
        ("Λ", "Lambda"),
        ("Ξ", "Xi"),
        ("Φ", "Phi"),
        ("Ψ", "Psi"),
        ("Ω", "Omega"),
    ]
    for symbol, replacement in symbol_replacements:
        text = text.replace(symbol, f" {replacement} " if replacement else "")

    # Typography normalization (direct replacement, no added spaces)
    typography = [
        ("–", "-"),   # en dash
        ("—", ", "),  # em dash to pause
        ("…", "..."),  # ellipsis
        ("'", "'"),   # curly apostrophe
        ("'", "'"),   # left single quote
        (""", '"'),   # curly quotes
        (""", '"'),
    ]
    for symbol, replacement in typography:
        text = text.replace(symbol, replacement)

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
