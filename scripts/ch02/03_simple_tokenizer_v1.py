"""Chapter 2.3: SimpleTokenizerV1

A basic tokenizer class that encodes text to token IDs and decodes back.
Requires a pre-built vocabulary. Does NOT handle unknown tokens.

Generates 3 cards:
- class_simple_tokenizer_v1_init.md
- method_simple_tokenizer_v1_encode.md
- method_simple_tokenizer_v1_decode.md
"""

import re
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# BUILD SAMPLE VOCABULARY
# =============================================================================

print_section("Building Sample Vocabulary")

sample_text = """It was the last he painted, you know. Mrs. Gisburn said
with pardonable pride."""

def preprocess(text: str) -> list[str]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [tok.strip() for tok in tokens if tok.strip()]

def build_vocab(tokens: list[str]) -> dict[str, int]:
    all_tokens = sorted(set(tokens))
    return {token: i for i, token in enumerate(all_tokens)}

tokens = preprocess(sample_text)
vocab = build_vocab(tokens)
print(f"Vocabulary size: {len(vocab)}")

# =============================================================================
# SIMPLETOKENIZERV1: __init__
# =============================================================================

print_section("SimpleTokenizerV1: __init__")

# The tokenizer stores two mappings:
# - str_to_int: for encoding (token -> ID)
# - int_to_str: for decoding (ID -> token)


class SimpleTokenizerV1:
    def __init__(self, vocab: dict[str, int]):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text: str) -> list[int]:
        tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
        tokens = [tok.strip() for tok in tokens if tok.strip()]
        return [self.str_to_int[s] for s in tokens]

    def decode(self, ids: list[int]) -> str:
        text = " ".join([self.int_to_str[i] for i in ids])
        return re.sub(r'\s+([,.:;?!"()\'])', r'\1', text)


tokenizer = SimpleTokenizerV1(vocab)
print(f"str_to_int entries: {len(tokenizer.str_to_int)}")
print(f"int_to_str entries: {len(tokenizer.int_to_str)}")
print()
print("Sample mappings:")
for tok in ["the", "last", ".", ","]:
    if tok in tokenizer.str_to_int:
        idx = tokenizer.str_to_int[tok]
        print(f"  {tok!r:6} -> {idx:3} -> {tokenizer.int_to_str[idx]!r}")

# =============================================================================
# SIMPLETOKENIZERV1: encode
# =============================================================================

print_section("SimpleTokenizerV1: encode")

test_text = "It was the last he painted, you know. Mrs. Gisburn said."
ids = tokenizer.encode(test_text)
print(f"Input:  {test_text!r}")
print(f"IDs:    {ids}")

# =============================================================================
# SIMPLETOKENIZERV1: decode
# =============================================================================

print_section("SimpleTokenizerV1: decode")

decoded = tokenizer.decode(ids)
print(f"IDs:     {ids}")
print(f"Decoded: {decoded!r}")

# Note: decode removes spaces before punctuation using regex substitution
print()
print("Without punctuation fix: " + repr(" ".join([tokenizer.int_to_str[i] for i in ids])))
print("With punctuation fix:    " + repr(decoded))

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: __init__
card1 = generate_card(
    filename="class_simple_tokenizer_v1_init.md",
    title="SimpleTokenizerV1: __init__",
    source="Build a LLM from Scratch, Chapter 2.3",
    context="""\
Initialize a tokenizer with forward (str->int) and inverse (int->str) mappings.
The inverse mapping is built by swapping key-value pairs from the vocab.""",
    code="""\
def __init__(self, vocab: dict[str, int]):
    self.str_to_int = vocab
    self.int_to_str = {i: s for s, i in vocab.items()}""",
    key_details="""\
- `str_to_int`: direct reference to vocab dict (for encoding)
- `int_to_str`: inverted dict comprehension `{i: s for s, i in vocab.items()}`
- Both needed: encode uses str_to_int, decode uses int_to_str""",
)
print_card_generated(card1)

# Card 2: encode
card2 = generate_card(
    filename="method_simple_tokenizer_v1_encode.md",
    title="SimpleTokenizerV1: encode",
    source="Build a LLM from Scratch, Chapter 2.3",
    context="""\
Encode text to token IDs: split with regex, clean up, then lookup each token.
Raises KeyError if token not in vocabulary.""",
    code=r"""def encode(self, text: str) -> list[int]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    tokens = [tok.strip() for tok in tokens if tok.strip()]
    return [self.str_to_int[s] for s in tokens]""",
    key_details="""\
- Same preprocessing as vocab building (split, strip, filter)
- List comprehension does the lookup: `self.str_to_int[s]`
- No error handling: unknown tokens cause KeyError""",
)
print_card_generated(card2)

# Card 3: decode
card3 = generate_card(
    filename="method_simple_tokenizer_v1_decode.md",
    title="SimpleTokenizerV1: decode",
    source="Build a LLM from Scratch, Chapter 2.3",
    context="""\
Decode token IDs back to text. Join with spaces, then fix punctuation spacing
using regex substitution.""",
    code=r"""def decode(self, ids: list[int]) -> str:
    text = " ".join([self.int_to_str[i] for i in ids])
    return re.sub(r'\s+([,.:;?!"()\'])', r'\1', text)""",
    key_details="""\
- First join all tokens with spaces: `" ".join([...])`
- `re.sub` removes space before punctuation
- Pattern `\\s+([punct])` captures punctuation, `\\1` keeps only the punctuation
- Result: `"Hello ,"` becomes `"Hello,"`""",
)
print_card_generated(card3)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
