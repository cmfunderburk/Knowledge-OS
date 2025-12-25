"""Chapter 2.6: create_dataloader_v1 - DataLoader Factory

A convenience function that creates a PyTorch DataLoader from raw text,
handling tokenization and batching.

Generates 1 card:
- function_create_dataloader_v1.md
"""

import tiktoken
import torch
from torch.utils.data import Dataset, DataLoader
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# GPTDatasetV1 (needed for the dataloader)
# =============================================================================


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


# =============================================================================
# create_dataloader_v1
# =============================================================================

print_section("create_dataloader_v1 Function")


def create_dataloader_v1(
    txt: str,
    batch_size: int = 4,
    max_length: int = 256,
    stride: int = 128,
    shuffle: bool = True,
    drop_last: bool = True,
    num_workers: int = 0,
):
    tokenizer = tiktoken.get_encoding("gpt2")
    dataset = GPTDatasetV1(txt, tokenizer, max_length, stride)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=drop_last,
        num_workers=num_workers,
    )
    return dataloader


# Demonstrate
sample_text = """In the heart of the city stood the old library, a relic
from a bygone era. Its stone walls bore the marks of time, and ivy clung
tightly to its facade. Inside, the musty scent of ancient books filled the
air, and the soft rustle of pages echoed through the hallowed halls."""

print("Creating dataloader...")
dataloader = create_dataloader_v1(
    sample_text,
    batch_size=2,
    max_length=8,
    stride=8,
    shuffle=False,
)

print(f"Dataset size: {len(dataloader.dataset)} samples")
print(f"Batch size: 2")
print(f"Number of batches: {len(dataloader)}")

# =============================================================================
# ITERATE OVER BATCHES
# =============================================================================

print_section("Iterating Over Batches")

for i, (inputs, targets) in enumerate(dataloader):
    print(f"Batch {i}:")
    print(f"  inputs.shape:  {inputs.shape}")
    print(f"  targets.shape: {targets.shape}")
    if i == 0:
        print(f"  inputs[0]:  {inputs[0].tolist()}")
        print(f"  targets[0]: {targets[0].tolist()}")
    if i >= 2:
        print("  ...")
        break

# =============================================================================
# KEY PARAMETERS EXPLAINED
# =============================================================================

print_section("Key Parameters")

print("batch_size=4    : Number of samples per batch")
print("max_length=256  : Context window size (tokens per sample)")
print("stride=128      : Step between windows (128 = 50% overlap)")
print("shuffle=True    : Randomize order each epoch")
print("drop_last=True  : Drop incomplete final batch (prevents loss spikes)")
print("num_workers=0   : CPU processes for data loading (0 = main process)")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

card = generate_card(
    filename="function_create_dataloader_v1.md",
    title="create_dataloader_v1: DataLoader Factory",
    source="Build a LLM from Scratch, Chapter 2.6",
    context="""\
A convenience function that creates a DataLoader from raw text.
Handles tokenization internally and returns batched input-target pairs.""",
    code="""\
def create_dataloader_v1(
    txt: str,
    batch_size: int = 4,
    max_length: int = 256,
    stride: int = 128,
    shuffle: bool = True,
    drop_last: bool = True,
    num_workers: int = 0,
):
    tokenizer = tiktoken.get_encoding("gpt2")
    dataset = GPTDatasetV1(txt, tokenizer, max_length, stride)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=drop_last,
        num_workers=num_workers,
    )
    return dataloader""",
    key_details="""\
- Creates tokenizer internally (gpt2 encoding)
- `drop_last=True`: drops incomplete final batch to prevent loss spikes
- `stride < max_length`: creates overlapping windows (more data, risk of overfit)
- `stride = max_length`: no overlap (recommended for training)
- Returns DataLoader yielding `(input_batch, target_batch)` tensors""",
)
print_card_generated(card)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
