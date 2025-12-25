"""Chapter 2.3: Building a Vocabulary

This script demonstrates how to build a vocabulary (token -> integer mapping)
from a list of tokens.

Generates 1 card:
- algorithm_vocab_from_tokens.md
"""

import re
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# PREPROCESS TEXT INTO TOKENS
# =============================================================================

print_section("Preprocessing Sample Text")

# Sample text (normally you'd load from file)
raw_text = """I HAD always thought Jack Gisburn rather a cheap genius--though
a good fellow enough--so it was no great surprise to me to hear that, in
the height of his glory, he had dropped painting."""

def preprocess(text: str) -> list[str]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [tok.strip() for tok in tokens if tok.strip()]

tokens = preprocess(raw_text)
print(f"Total tokens: {len(tokens)}")
print(f"First 20: {tokens[:20]}")

# =============================================================================
# BUILD VOCABULARY
# =============================================================================

print_section("Building Vocabulary")

# The vocabulary maps each unique token to a unique integer ID.
# We sort alphabetically for deterministic ordering.

def build_vocab(tokens: list[str]) -> dict[str, int]:
    """Build vocabulary from tokens: sorted unique tokens -> integer IDs."""
    all_tokens = sorted(set(tokens))
    return {token: i for i, token in enumerate(all_tokens)}

vocab = build_vocab(tokens)
print(f"Vocabulary size: {len(vocab)}")
print()
print("First 10 entries:")
for i, (token, idx) in enumerate(vocab.items()):
    if i >= 10:
        break
    print(f"  {token!r:12} -> {idx}")

print()
print("Last 5 entries:")
items = list(vocab.items())
for token, idx in items[-5:]:
    print(f"  {token!r:12} -> {idx}")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

card = generate_card(
    filename="algorithm_vocab_from_tokens.md",
    title="Build Vocabulary from Tokens",
    source="Build a LLM from Scratch, Chapter 2.3",
    context="""\
A vocabulary maps each unique token to a unique integer ID.
Tokens are sorted alphabetically for deterministic ordering.""",
    code="""\
def build_vocab(tokens: list[str]) -> dict[str, int]:
    all_tokens = sorted(set(tokens))
    return {token: i for i, token in enumerate(all_tokens)}""",
    key_details="""\
- `set(tokens)` extracts unique tokens
- `sorted()` ensures deterministic ordering (alphabetical)
- `enumerate()` assigns sequential integer IDs starting from 0
- Dict comprehension builds the final mapping""",
)
print_card_generated(card)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
