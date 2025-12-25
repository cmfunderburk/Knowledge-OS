"""Chapter 2.8: Positional Embeddings

Positional embeddings encode token positions in a sequence, since
self-attention is inherently position-agnostic.

Generates 2 cards:
- pattern_positional_embedding_create.md
- pattern_input_embeddings_combine.md
"""

import torch
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# WHY POSITIONAL EMBEDDINGS?
# =============================================================================

print_section("Why Positional Embeddings?")

print("""Token embeddings map the same token to the same vector,
regardless of position:

  "The cat sat" -> [emb(The), emb(cat), emb(sat)]
  "cat The sat" -> [emb(cat), emb(The), emb(sat)]

Self-attention treats these as bag-of-tokens (permutation invariant).
But word order matters! "The cat sat" != "cat The sat"

Solution: Add position-specific vectors to token embeddings.""")

# =============================================================================
# CREATE POSITIONAL EMBEDDING LAYER
# =============================================================================

print_section("Create Positional Embedding Layer")

# Parameters
context_length = 4   # Maximum sequence length
output_dim = 256     # Same as token embedding dimension

# Create the layer
torch.manual_seed(123)
pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)

print(f"context_length: {context_length}")
print(f"output_dim: {output_dim}")
print(f"Layer: {pos_embedding_layer}")
print()
print(f"Weight matrix shape: {pos_embedding_layer.weight.shape}")
print(f"  - {context_length} rows (one per position)")
print(f"  - {output_dim} columns (same as token embeddings)")

# =============================================================================
# GENERATE POSITION INDICES
# =============================================================================

print_section("Generate Position Indices with torch.arange")

# Create position indices: [0, 1, 2, ..., context_length-1]
positions = torch.arange(context_length)
print(f"positions = torch.arange({context_length})")
print(f"Result: {positions.tolist()}")
print()

# Look up positional embeddings
pos_embeddings = pos_embedding_layer(positions)
print(f"Positional embeddings shape: {pos_embeddings.shape}")
print(f"  - {context_length} positions")
print(f"  - {output_dim} dimensions each")

# =============================================================================
# COMBINE TOKEN + POSITIONAL EMBEDDINGS
# =============================================================================

print_section("Combine Token + Positional Embeddings")

# Create token embedding layer
vocab_size = 50257
token_embedding_layer = torch.nn.Embedding(vocab_size, output_dim)

# Sample input: batch of 2 sequences, 4 tokens each
input_ids = torch.tensor([
    [40, 367, 2885, 1464],
    [1807, 3619, 402, 271],
])
print(f"Input IDs shape: {input_ids.shape}  # (batch=2, seq=4)")

# Get token embeddings
token_embeddings = token_embedding_layer(input_ids)
print(f"Token embeddings shape: {token_embeddings.shape}")

# Get positional embeddings (same for all sequences in batch)
pos_embeddings = pos_embedding_layer(torch.arange(context_length))
print(f"Positional embeddings shape: {pos_embeddings.shape}")

# Combine by addition (broadcasting handles batch dimension)
input_embeddings = token_embeddings + pos_embeddings
print(f"Input embeddings shape: {input_embeddings.shape}")

print()
print("Broadcasting: (2, 4, 256) + (4, 256) -> (2, 4, 256)")
print("Position embeddings are added to each sequence in the batch.")

# =============================================================================
# ABSOLUTE VS RELATIVE POSITIONAL EMBEDDINGS
# =============================================================================

print_section("Absolute vs Relative Positional Embeddings")

print("""GPT models use ABSOLUTE positional embeddings:
  - Position 0 always gets the same positional vector
  - Position 1 always gets its own vector, etc.
  - Learned during training (not fixed sinusoidal)

Alternative: RELATIVE positional embeddings:
  - Encode distance between tokens, not absolute position
  - Used in some newer architectures (e.g., RoPE in LLaMA)
  - Better generalization to longer sequences""")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: Create positional embedding layer
card1 = generate_card(
    filename="pattern_positional_embedding_create.md",
    title="Create Positional Embedding Layer",
    source="Build a LLM from Scratch, Chapter 2.8",
    context="""\
Positional embeddings encode sequence position. Create a layer with
context_length positions, same embedding dimension as token embeddings.""",
    code="""\
context_length = 4  # Max sequence length
output_dim = 256    # Same as token embedding dim

pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)
pos_embeddings = pos_embedding_layer(torch.arange(context_length))""",
    key_details="""\
- First arg is `context_length`, not vocab_size
- `output_dim` must match token embedding dimension (for addition)
- `torch.arange(context_length)` creates position indices [0, 1, 2, ...]
- GPT uses learned (not sinusoidal) positional embeddings
- Limits max sequence length the model can handle""",
)
print_card_generated(card1)

# Card 2: Combine embeddings
card2 = generate_card(
    filename="pattern_input_embeddings_combine.md",
    title="Combine Token and Positional Embeddings",
    source="Build a LLM from Scratch, Chapter 2.8",
    context="""\
The final input to the transformer is token embeddings + positional embeddings.
Broadcasting handles batched inputs automatically.""",
    code="""\
# token_embeddings: (batch, seq_len, embed_dim)
# pos_embeddings:   (seq_len, embed_dim)
input_embeddings = token_embeddings + pos_embeddings""",
    key_details="""\
- Simple element-wise addition
- Broadcasting: `(batch, seq, dim) + (seq, dim)` -> `(batch, seq, dim)`
- Same positional embeddings added to every sequence in batch
- Result shape: `(batch_size, seq_length, embed_dim)`
- This is the input to the first transformer block""",
)
print_card_generated(card2)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
