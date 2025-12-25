"""Chapter 2: Working with Text Data - Example script.

This script demonstrates the key concepts from Chapter 2:
1. Simple tokenization with regex
2. Building vocabularies
3. BPE tokenization with tiktoken
4. Data loading with sliding window
5. Token embeddings and positional embeddings
"""

from pathlib import Path

import tiktoken
import torch

from llm_scratch import (
    SimpleTokenizerV1,
    SimpleTokenizerV2,
    build_vocab_from_text,
    build_vocab_with_special_tokens,
    create_dataloader_v1,
)


def main():
    # Load the sample text
    data_path = Path(__file__).parent.parent / "data" / "the-verdict.txt"
    with open(data_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"Total characters: {len(raw_text)}")
    print(f"First 100 chars: {raw_text[:100]!r}")
    print()

    # --- Section 2.3: Simple Tokenization ---
    print("=" * 60)
    print("Simple Tokenization (SimpleTokenizerV1)")
    print("=" * 60)

    vocab = build_vocab_from_text(raw_text)
    print(f"Vocabulary size: {len(vocab)}")

    tokenizer_v1 = SimpleTokenizerV1(vocab)
    sample_text = '"It\'s the last he painted, you know," Mrs. Gisburn said with pardonable pride.'
    ids = tokenizer_v1.encode(sample_text)
    print(f"\nSample: {sample_text}")
    print(f"Token IDs: {ids[:10]}... (showing first 10)")
    print(f"Decoded: {tokenizer_v1.decode(ids)}")
    print()

    # --- Section 2.4: Handling Unknown Words ---
    print("=" * 60)
    print("Handling Unknown Words (SimpleTokenizerV2)")
    print("=" * 60)

    vocab_with_special = build_vocab_with_special_tokens(raw_text)
    print(f"Vocabulary size (with special tokens): {len(vocab_with_special)}")

    tokenizer_v2 = SimpleTokenizerV2(vocab_with_special)
    test_text = "Hello, do you like tea? <|endoftext|> In the sunlit terraces of the palace."
    ids = tokenizer_v2.encode(test_text)
    decoded = tokenizer_v2.decode(ids)
    print(f"\nOriginal: {test_text}")
    print(f"Decoded:  {decoded}")
    print("(Notice 'Hello' and 'palace' become <|unk|>)")
    print()

    # --- Section 2.5: BPE Tokenization ---
    print("=" * 60)
    print("BPE Tokenization (tiktoken)")
    print("=" * 60)

    bpe_tokenizer = tiktoken.get_encoding("gpt2")
    text = "Hello, do you like tea? <|endoftext|> In the sunlit terraces of someunknownPlace."
    integers = bpe_tokenizer.encode(text, allowed_special={"<|endoftext|>"})
    print(f"BPE vocabulary size: {bpe_tokenizer.n_vocab}")
    print(f"\nText: {text}")
    print(f"Token IDs: {integers}")
    print(f"Decoded: {bpe_tokenizer.decode(integers)}")
    print()

    # --- Section 2.6: Data Sampling with Sliding Window ---
    print("=" * 60)
    print("Data Loading with Sliding Window")
    print("=" * 60)

    dataloader = create_dataloader_v1(
        raw_text, batch_size=8, max_length=4, stride=4, shuffle=False
    )

    data_iter = iter(dataloader)
    inputs, targets = next(data_iter)
    print(f"Batch shape: {inputs.shape}")
    print(f"\nFirst batch inputs:\n{inputs}")
    print(f"\nFirst batch targets:\n{targets}")
    print()

    # --- Section 2.7-2.8: Embeddings ---
    print("=" * 60)
    print("Token and Positional Embeddings")
    print("=" * 60)

    vocab_size = 50257  # BPE vocabulary size
    output_dim = 256  # Embedding dimension
    context_length = 4  # Same as max_length above

    # Token embedding layer
    token_embedding_layer = torch.nn.Embedding(vocab_size, output_dim)
    token_embeddings = token_embedding_layer(inputs)
    print(f"Token embeddings shape: {token_embeddings.shape}")

    # Positional embedding layer
    pos_embedding_layer = torch.nn.Embedding(context_length, output_dim)
    pos_embeddings = pos_embedding_layer(torch.arange(context_length))
    print(f"Positional embeddings shape: {pos_embeddings.shape}")

    # Combined input embeddings
    input_embeddings = token_embeddings + pos_embeddings
    print(f"Input embeddings shape: {input_embeddings.shape}")
    print()


if __name__ == "__main__":
    main()
