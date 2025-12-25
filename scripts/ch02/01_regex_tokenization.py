"""Chapter 2.2: Regex-based Tokenization

This script demonstrates the regex pattern used to split text into tokens.
The pattern handles words, punctuation, whitespace, and special cases like
double-dashes.

Generates 2 cards:
- algorithm_tokenization_regex_pattern.md
- algorithm_tokenization_preprocessing.md
"""

import re
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# THE REGEX PATTERN
# =============================================================================

print_section("The Tokenization Regex Pattern")

# This pattern captures:
# - Punctuation: , . : ; ? _ ! " ( ) '
# - Double-dash: --
# - Whitespace: \s
#
# The parentheses make these CAPTURED groups, so they appear in the output
# rather than being used only as split points.

TOKENIZER_PATTERN = r'([,.:;?_!"()\']|--|\s)'

text = "Hello, world. Is this-- a test?"
result = re.split(TOKENIZER_PATTERN, text)
print(f"Input:  {text!r}")
print(f"Split:  {result}")

# =============================================================================
# THE PREPROCESSING PIPELINE
# =============================================================================

print_section("The Preprocessing Pipeline")

# After splitting, we need to:
# 1. Strip whitespace from each token
# 2. Filter out empty strings

def preprocess(text: str) -> list[str]:
    """Split text into tokens and clean up."""
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [tok.strip() for tok in tokens if tok.strip()]

tokens = preprocess(text)
print(f"Input:  {text!r}")
print(f"Tokens: {tokens}")

# Demonstrate on more complex text
complex_text = '"It\'s the last he painted, you know," Mrs. Gisburn said.'
complex_tokens = preprocess(complex_text)
print()
print(f"Input:  {complex_text!r}")
print(f"Tokens: {complex_tokens}")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: The regex pattern
card1 = generate_card(
    filename="algorithm_tokenization_regex_pattern.md",
    title="Tokenization Regex Pattern",
    source="Build a LLM from Scratch, Chapter 2.2",
    context="""\
A regex pattern that splits text into tokens while preserving punctuation
as separate tokens. Uses capturing groups so delimiters appear in output.""",
    code=r"""TOKENIZER_PATTERN = r'([,.:;?_!"()\']|--|\s)'""",
    key_details="""\
- Parentheses create a capturing group (delimiters kept in output)
- Character class `[,.:;?_!"()\\']` matches single punctuation
- `--` handles double-dash as single token
- `\\s` matches any whitespace""",
)
print_card_generated(card1)

# Card 2: The preprocessing pipeline
card2 = generate_card(
    filename="algorithm_tokenization_preprocessing.md",
    title="Tokenization Preprocessing Pipeline",
    source="Build a LLM from Scratch, Chapter 2.2",
    context="""\
After regex splitting, clean up tokens by stripping whitespace and
removing empty strings.""",
    code=r"""def preprocess(text: str) -> list[str]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [tok.strip() for tok in tokens if tok.strip()]""",
    key_details="""\
- `strip()` removes leading/trailing whitespace from each token
- `if tok.strip()` filters out empty strings and whitespace-only tokens
- Returns clean list of words and punctuation""",
)
print_card_generated(card2)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
