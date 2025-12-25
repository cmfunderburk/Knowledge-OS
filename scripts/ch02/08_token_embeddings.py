"""Chapter 2.7: Token Embeddings

Token embeddings convert discrete token IDs into continuous vector
representations that neural networks can process.

Generates 2 cards:
- pattern_embedding_layer_create.md
- pattern_embedding_layer_lookup.md
"""

import torch
from _card_generator import generate_card, print_card_generated, print_section

# =============================================================================
# WHY EMBEDDINGS?
# =============================================================================

print_section("Why Embeddings?")

print("""Neural networks require continuous numerical inputs.
Token IDs are discrete integers (0, 1, 2, ...).
Embeddings map each token ID to a learnable vector.

The embedding layer is essentially a lookup table:
  token_id -> embedding_vector

During training, these vectors are optimized to capture
semantic relationships between tokens.""")

# =============================================================================
# CREATE EMBEDDING LAYER
# =============================================================================

print_section("Create Embedding Layer")

# Parameters
vocab_size = 50257  # GPT-2 vocabulary size
output_dim = 256    # Embedding dimension (GPT-3 uses 12,288)

# Create the layer
torch.manual_seed(123)  # For reproducibility
token_embedding_layer = torch.nn.Embedding(vocab_size, output_dim)

print(f"vocab_size: {vocab_size}")
print(f"output_dim: {output_dim}")
print(f"Layer: {token_embedding_layer}")
print()

# The embedding layer has a weight matrix
print(f"Weight matrix shape: {token_embedding_layer.weight.shape}")
print(f"  - {vocab_size} rows (one per token)")
print(f"  - {output_dim} columns (embedding dimensions)")

# =============================================================================
# EMBEDDING LOOKUP
# =============================================================================

print_section("Embedding Lookup")

# Sample token IDs (from a batch)
input_ids = torch.tensor([40, 367, 2885, 1464])
print(f"Input IDs: {input_ids.tolist()}")
print(f"Input shape: {input_ids.shape}")
print()

# Look up embeddings
token_embeddings = token_embedding_layer(input_ids)
print(f"Output shape: {token_embeddings.shape}")
print(f"  - 4 tokens")
print(f"  - {output_dim} dimensions each")

# Show a few values
print()
print(f"First token (ID=40) embedding[:5]: {token_embeddings[0, :5].tolist()}")

# =============================================================================
# BATCH EMBEDDING
# =============================================================================

print_section("Batch Embedding")

# Batched input: (batch_size, seq_length)
batch_ids = torch.tensor([
    [40, 367, 2885, 1464],
    [1807, 3619, 402, 271],
])
print(f"Batch shape: {batch_ids.shape}  # (batch_size=2, seq_length=4)")

batch_embeddings = token_embedding_layer(batch_ids)
print(f"Output shape: {batch_embeddings.shape}  # (batch, seq, embed_dim)")

# =============================================================================
# EMBEDDING IS A LOOKUP
# =============================================================================

print_section("Embedding = Weight Matrix Lookup")

# The embedding of token ID i is row i of the weight matrix
token_id = 40
embedding_via_layer = token_embedding_layer(torch.tensor([token_id]))[0]
embedding_via_weight = token_embedding_layer.weight[token_id]

print(f"Token ID: {token_id}")
print(f"Via layer call: {embedding_via_layer[:5].tolist()}")
print(f"Via weight[id]: {embedding_via_weight[:5].tolist()}")
print(f"Equal: {torch.allclose(embedding_via_layer, embedding_via_weight)}")

# =============================================================================
# GENERATE CARDS
# =============================================================================

print_section("Generating Cards")

# Card 1: Create embedding layer
card1 = generate_card(
    filename="pattern_embedding_layer_create.md",
    title="Create Token Embedding Layer",
    source="Build a LLM from Scratch, Chapter 2.7",
    context="""\
An embedding layer maps discrete token IDs to continuous vectors.
It's a learnable lookup table with shape (vocab_size, embedding_dim).""",
    code="""\
vocab_size = 50257  # GPT-2 vocabulary size
output_dim = 256    # Embedding dimension

token_embedding_layer = torch.nn.Embedding(vocab_size, output_dim)""",
    key_details="""\
- `vocab_size`: number of unique tokens (rows in weight matrix)
- `output_dim`: embedding dimension (columns in weight matrix)
- Weight matrix shape: `(vocab_size, output_dim)`
- Weights initialized randomly, learned during training
- GPT-2 small: 768 dim, GPT-3 175B: 12,288 dim""",
)
print_card_generated(card1)

# Card 2: Embedding lookup
card2 = generate_card(
    filename="pattern_embedding_layer_lookup.md",
    title="Token Embedding Lookup",
    source="Build a LLM from Scratch, Chapter 2.7",
    context="""\
Pass token IDs through the embedding layer to get vectors.
Works with single sequences or batches.""",
    code="""\
# input_ids shape: (seq_length,) or (batch_size, seq_length)
token_embeddings = token_embedding_layer(input_ids)
# output shape: (seq_length, embed_dim) or (batch, seq, embed_dim)""",
    key_details="""\
- Input: tensor of integer token IDs
- Output: tensor of embedding vectors
- Shape transformation: adds `embed_dim` as final dimension
- Equivalent to indexing weight matrix: `layer.weight[token_id]`
- Gradients flow back to update the weight matrix during training""",
)
print_card_generated(card2)

print()
print("Done! Review cards in: ~/Dropbox/Apps/KnOS/solutions/wip/")
