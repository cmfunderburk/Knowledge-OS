"""Chapter 2.4: SimpleTokenizerV2

Extends SimpleTokenizerV1 to handle unknown tokens with <|unk|>.
The key difference is in the encode method.

Generates 1 card:
- method_simple_tokenizer_v2_encode.md
"""

import re
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# BUILD VOCABULARY WITH SPECIAL TOKENS
# =============================================================================

print_section("Building Vocabulary with Special Tokens")

sample_text = """In the sunlit terraces of the palace. The verdict was final."""

def preprocess(text: str) -> list[str]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    return [tok.strip() for tok in tokens if tok.strip()]

tokens = preprocess(sample_text)
all_tokens = sorted(set(tokens))

# Add special tokens
all_tokens.extend(["<|endoftext|>", "<|unk|>"])

vocab = {token: i for i, token in enumerate(all_tokens)}
print(f"Vocabulary size: {len(vocab)}")
print()
print("Special tokens:")
print(f"  <|endoftext|> -> {vocab['<|endoftext|>']}")
print(f"  <|unk|>       -> {vocab['<|unk|>']}")

# =============================================================================
# THE PROBLEM: Unknown Tokens
# =============================================================================

print_section("The Problem: Unknown Tokens")

# SimpleTokenizerV1 crashes on unknown tokens
class SimpleTokenizerV1:
    def __init__(self, vocab: dict[str, int]):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text: str) -> list[int]:
        tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
        tokens = [tok.strip() for tok in tokens if tok.strip()]
        return [self.str_to_int[s] for s in tokens]  # KeyError on unknown!

test_text = "Hello, do you like tea?"
print(f"Test: {test_text!r}")
print()

try:
    tokenizer_v1 = SimpleTokenizerV1(vocab)
    tokenizer_v1.encode(test_text)
except KeyError as e:
    print(f"V1 raises KeyError: {e}")
    print("'Hello' is not in our small vocabulary!")

# =============================================================================
# THE SOLUTION: SimpleTokenizerV2
# =============================================================================

print_section("The Solution: SimpleTokenizerV2")


class SimpleTokenizerV2:
    def __init__(self, vocab: dict[str, int]):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text: str) -> list[int]:
        tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
        tokens = [tok.strip() for tok in tokens if tok.strip()]
        # Replace unknown tokens with <|unk|>
        tokens = [tok if tok in self.str_to_int else "<|unk|>" for tok in tokens]
        return [self.str_to_int[s] for s in tokens]

    def decode(self, ids: list[int]) -> str:
        text = " ".join([self.int_to_str[i] for i in ids])
        return re.sub(r'\s+([,.:;?!"()\'])', r'\1', text)


tokenizer_v2 = SimpleTokenizerV2(vocab)
ids = tokenizer_v2.encode(test_text)
decoded = tokenizer_v2.decode(ids)

print(f"Input:   {test_text!r}")
print(f"IDs:     {ids}")
print(f"Decoded: {decoded!r}")
print()
print("Unknown words 'Hello', 'do', 'you', 'like', 'tea' all become <|unk|>")

# =============================================================================
# DEMONSTRATE <|endoftext|>
# =============================================================================

print_section("Using <|endoftext|> Between Documents")

text1 = "The verdict was final."
text2 = "In the sunlit terraces."
combined = f"{text1} <|endoftext|> {text2}"

ids = tokenizer_v2.encode(combined)
decoded = tokenizer_v2.decode(ids)
print(f"Combined: {combined!r}")
print(f"IDs:      {ids}")
print(f"Decoded:  {decoded!r}")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

card = generate_card(
    filename="method_simple_tokenizer_v2_encode.md",
    title="SimpleTokenizerV2: encode with Unknown Handling",
    source="Build a LLM from Scratch, Chapter 2.4",
    context="""\
Extends V1's encode to handle unknown tokens by replacing them with <|unk|>.
Requires vocabulary to include the <|unk|> special token.""",
    code=r"""def encode(self, text: str) -> list[int]:
    tokens = re.split(r'([,.:;?_!"()\']|--|\s)', text)
    tokens = [tok.strip() for tok in tokens if tok.strip()]
    tokens = [tok if tok in self.str_to_int else "<|unk|>" for tok in tokens]
    return [self.str_to_int[s] for s in tokens]""",
    key_details="""\
- Key addition: conditional replacement before lookup
- `tok if tok in self.str_to_int else "<|unk|>"`
- Vocab must include `<|unk|>` token (added during vocab building)
- Prevents KeyError on unknown tokens""",
)
print_card_generated(card)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
