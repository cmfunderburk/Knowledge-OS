"""Chapter 2.6: GPTDatasetV1 - Sliding Window Dataset

A PyTorch Dataset that creates input-target pairs using a sliding window
over tokenized text. This is how training data is prepared for next-word
prediction.

Generates 2 cards:
- class_gpt_dataset_v1_init.md
- class_gpt_dataset_v1_methods.md
"""

import tiktoken
import torch
from torch.utils.data import Dataset
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# THE SLIDING WINDOW CONCEPT
# =============================================================================

print_section("The Sliding Window Concept")

# For next-word prediction, we need (input, target) pairs where
# target is input shifted by 1 position.

sample_ids = [40, 367, 2885, 1464, 1807, 3619, 402]
max_length = 4
stride = 2

print(f"Token IDs: {sample_ids}")
print(f"max_length={max_length}, stride={stride}")
print()

print("Sliding window creates these pairs:")
for i in range(0, len(sample_ids) - max_length, stride):
    input_chunk = sample_ids[i : i + max_length]
    target_chunk = sample_ids[i + 1 : i + max_length + 1]
    print(f"  Input:  {input_chunk}")
    print(f"  Target: {target_chunk}")
    print()

# =============================================================================
# GPTDatasetV1: __init__
# =============================================================================

print_section("GPTDatasetV1: __init__")


class GPTDatasetV1(Dataset):
    def __init__(self, txt: str, tokenizer, max_length: int, stride: int):
        self.input_ids = []
        self.target_ids = []

        token_ids = tokenizer.encode(txt)

        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i : i + max_length]
            target_chunk = token_ids[i + 1 : i + max_length + 1]
            self.input_ids.append(torch.tensor(input_chunk))
            self.target_ids.append(torch.tensor(target_chunk))

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return self.input_ids[idx], self.target_ids[idx]


# Demonstrate
tokenizer = tiktoken.get_encoding("gpt2")
sample_text = "In the heart of the city stood the old library."

dataset = GPTDatasetV1(sample_text, tokenizer, max_length=4, stride=4)
print(f"Text: {sample_text!r}")
print(f"Dataset size: {len(dataset)} samples")
print()

for i in range(min(3, len(dataset))):
    inp, tgt = dataset[i]
    print(f"Sample {i}:")
    print(f"  Input:  {inp.tolist()}")
    print(f"  Target: {tgt.tolist()}")

# =============================================================================
# GPTDatasetV1: __len__ and __getitem__
# =============================================================================

print_section("GPTDatasetV1: __len__ and __getitem__")

print("__len__ returns number of samples:")
print(f"  len(dataset) = {len(dataset)}")
print()

print("__getitem__ returns (input_tensor, target_tensor):")
inp, tgt = dataset[0]
print(f"  dataset[0] = ({inp}, {tgt})")
print(f"  Types: {type(inp).__name__}, {type(tgt).__name__}")

# =============================================================================
# STRIDE EFFECTS
# =============================================================================

print_section("Effect of Stride")

# stride=1: maximum overlap, more samples
ds_stride1 = GPTDatasetV1(sample_text, tokenizer, max_length=4, stride=1)
print(f"stride=1: {len(ds_stride1)} samples (maximum, overlapping)")

# stride=max_length: no overlap
ds_stride4 = GPTDatasetV1(sample_text, tokenizer, max_length=4, stride=4)
print(f"stride=4: {len(ds_stride4)} samples (no overlap)")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: __init__ with sliding window
card1 = generate_card(
    filename="class_gpt_dataset_v1_init.md",
    title="GPTDatasetV1: __init__ with Sliding Window",
    source="Build a LLM from Scratch, Chapter 2.6",
    context="""\
A PyTorch Dataset that tokenizes text and creates input-target pairs
using a sliding window. Targets are inputs shifted by 1 position.""",
    code="""\
def __init__(self, txt: str, tokenizer, max_length: int, stride: int):
    self.input_ids = []
    self.target_ids = []

    token_ids = tokenizer.encode(txt)

    for i in range(0, len(token_ids) - max_length, stride):
        input_chunk = token_ids[i : i + max_length]
        target_chunk = token_ids[i + 1 : i + max_length + 1]
        self.input_ids.append(torch.tensor(input_chunk))
        self.target_ids.append(torch.tensor(target_chunk))""",
    key_details="""\
- `max_length`: context window size (how many tokens per sample)
- `stride`: step size between windows (stride=max_length means no overlap)
- Target is input shifted by 1: `[i+1 : i+max_length+1]`
- Range stops at `len(token_ids) - max_length` to avoid incomplete windows
- Each chunk stored as `torch.tensor`""",
)
print_card_generated(card1)

# Card 2: __len__ and __getitem__
card2 = generate_card(
    filename="class_gpt_dataset_v1_methods.md",
    title="GPTDatasetV1: __len__ and __getitem__",
    source="Build a LLM from Scratch, Chapter 2.6",
    context="""\
Required PyTorch Dataset methods. __len__ returns dataset size,
__getitem__ returns (input, target) tensor pair for a given index.""",
    code="""\
def __len__(self):
    return len(self.input_ids)

def __getitem__(self, idx):
    return self.input_ids[idx], self.target_ids[idx]""",
    key_details="""\
- `__len__`: enables `len(dataset)` and is required by DataLoader
- `__getitem__`: enables indexing `dataset[i]` and iteration
- Returns tuple: (input_tensor, target_tensor)
- Both tensors have shape `(max_length,)`""",
)
print_card_generated(card2)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
