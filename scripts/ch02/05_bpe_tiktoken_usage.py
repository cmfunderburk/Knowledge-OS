"""Chapter 2.5: BPE Tokenization with tiktoken

Demonstrates using OpenAI's tiktoken library for Byte Pair Encoding (BPE)
tokenization, as used in GPT-2, GPT-3, and ChatGPT.

Generates 3 cards:
- pattern_tiktoken_instantiate.md
- pattern_tiktoken_encode.md
- pattern_tiktoken_decode.md
"""

import tiktoken
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# INSTANTIATE TOKENIZER
# =============================================================================

print_section("Instantiate BPE Tokenizer")

# tiktoken provides pre-trained BPE tokenizers
# "gpt2" encoding is used by GPT-2 and GPT-3

tokenizer = tiktoken.get_encoding("gpt2")

print(f"Encoding: gpt2")
print(f"Vocabulary size: {tokenizer.n_vocab}")
print(f"Special tokens: <|endoftext|> = {tokenizer.encode('<|endoftext|>', allowed_special={'<|endoftext|>'})}")

# =============================================================================
# ENCODE TEXT
# =============================================================================

print_section("Encode Text to Token IDs")

text = "Hello, do you like tea? <|endoftext|> In the sunlit terraces of someunknownPlace."

# Must explicitly allow special tokens, otherwise they're treated as text
ids = tokenizer.encode(text, allowed_special={"<|endoftext|>"})

print(f"Text: {text!r}")
print(f"IDs:  {ids}")
print(f"Count: {len(ids)} tokens")

# =============================================================================
# BPE HANDLES UNKNOWN WORDS
# =============================================================================

print_section("BPE Handles Unknown Words via Subwords")

# Unlike SimpleTokenizerV2, BPE doesn't need <|unk|>
# It breaks unknown words into subword units

unknown_word = "someunknownPlace"
ids_unknown = tokenizer.encode(unknown_word)
print(f"Word: {unknown_word!r}")
print(f"IDs:  {ids_unknown}")
print()
print("Subword breakdown:")
for token_id in ids_unknown:
    subword = tokenizer.decode([token_id])
    print(f"  {token_id:5} -> {subword!r}")

# Another example from the book
print()
gibberish = "Akwirw ier"
ids_gib = tokenizer.encode(gibberish)
print(f"Word: {gibberish!r}")
print(f"IDs:  {ids_gib}")
print("Subwords:", [tokenizer.decode([i]) for i in ids_gib])

# =============================================================================
# DECODE BACK TO TEXT
# =============================================================================

print_section("Decode Token IDs to Text")

# Full roundtrip
original = "Hello, do you like tea? <|endoftext|> In the sunlit terraces."
ids = tokenizer.encode(original, allowed_special={"<|endoftext|>"})
decoded = tokenizer.decode(ids)

print(f"Original: {original!r}")
print(f"IDs:      {ids}")
print(f"Decoded:  {decoded!r}")
print(f"Match:    {original == decoded}")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: Instantiate
card1 = generate_card(
    filename="pattern_tiktoken_instantiate.md",
    title="tiktoken: Instantiate BPE Tokenizer",
    source="Build a LLM from Scratch, Chapter 2.5",
    context="""\
tiktoken provides pre-trained BPE tokenizers used by OpenAI models.
The "gpt2" encoding is used by GPT-2, GPT-3, and ChatGPT.""",
    code="""\
import tiktoken

tokenizer = tiktoken.get_encoding("gpt2")""",
    key_details="""\
- `get_encoding()` not `get_tokenizer()` or similar
- "gpt2" is the encoding name (also: "cl100k_base" for GPT-4)
- `tokenizer.n_vocab` gives vocabulary size (50,257 for GPT-2)""",
)
print_card_generated(card1)

# Card 2: Encode
card2 = generate_card(
    filename="pattern_tiktoken_encode.md",
    title="tiktoken: Encode with Special Tokens",
    source="Build a LLM from Scratch, Chapter 2.5",
    context="""\
Encode text to token IDs. Special tokens like <|endoftext|> must be
explicitly allowed, otherwise they're treated as regular text.""",
    code="""\
ids = tokenizer.encode(text, allowed_special={"<|endoftext|>"})""",
    key_details="""\
- `allowed_special` is a set of special tokens to recognize
- Without it, `<|endoftext|>` becomes multiple regular tokens
- BPE handles unknown words by breaking into subwords (no <|unk|> needed)
- Returns list of integers""",
)
print_card_generated(card2)

# Card 3: Decode
card3 = generate_card(
    filename="pattern_tiktoken_decode.md",
    title="tiktoken: Decode Token IDs",
    source="Build a LLM from Scratch, Chapter 2.5",
    context="""\
Decode token IDs back to text. Works with any valid token IDs,
including subword tokens from BPE decomposition.""",
    code="""\
text = tokenizer.decode(ids)""",
    key_details="""\
- Takes list of integers, returns string
- Subwords are automatically reassembled
- Roundtrip: `decode(encode(text)) == text` (for allowed specials)
- Can decode single tokens: `tokenizer.decode([token_id])`""",
)
print_card_generated(card3)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
