# Getting Started

Complete setup guide for Knowledge OS.

## Requirements

Before installing, ensure you have:

- **Python 3.11** — Verify with `python3 --version`
- **uv** — Python package manager
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Or see [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)
- **Gemini API Key** — Required for the Reader module
  - Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey)
  - Free tier: 1500 requests/day (sufficient for typical self-study)

### Optional: Voice Features

Voice input and text-to-speech require additional dependencies:

- **CUDA-capable GPU** with 1-4GB VRAM (depending on TTS backend)
- **Linux, macOS ARM64, or Windows** (PyTorch platform requirement)

## Installation

```bash
# Clone the repository
git clone https://github.com/cmfunderburk/Knowledge-OS
cd Knowledge-OS

# Install core dependencies
uv sync

# Optional: Install voice features
uv sync --extra voice       # Voice input + Kokoro TTS (~1GB VRAM)
uv sync --extra chatterbox  # Voice + Chatterbox TTS (~3-4GB VRAM)
```

## Initial Setup

Run the interactive setup to create your configuration files:

```bash
uv run knos init
```

This creates three files in `config/`:

| File | Purpose |
|------|---------|
| `reader.yaml` | Gemini API key, voice/TTS settings |
| `content.yaml` | Registered reading materials |
| `study.yaml` | Study schedule and phases (optional) |

The setup will prompt for your Gemini API key. You can also set it via the `GOOGLE_API_KEY` environment variable.

### Verify Setup

Test that the LLM connection works:

```bash
uv run knos read test
```

If this fails, see [Troubleshooting](TROUBLESHOOTING.md).

## Your First Session

### Quick Path: Bundled Classics (Recommended)

Three classics from Project Gutenberg and five foundational articles are bundled and work immediately after `knos init`:

```bash
uv run knos read
```

Select a material (e.g., "Nicomachean Ethics"), then a chapter. The tutor opens with a question about the reading.

**Bundled classics:**
- Nicomachean Ethics — Aristotle
- Don Quixote — Cervantes
- The Brothers Karamazov — Dostoevsky

**Bundled articles:**
- Attention Is All You Need (Transformer paper)
- Einstein's Photoelectric Effect (1905)
- Mendel's Plant Hybridization (1866)
- William James, "What is an Emotion?" (1884)
- Wittgenstein, "Some Remarks on Logical Form" (1929)
- Stringfellow Barr, "Notes on Dialogue" (1968)

### Adding Your Own EPUB (Easiest)

EPUBs are the easiest format—chapter structure is extracted automatically.

1. Create a directory and place your EPUB:
   ```bash
   mkdir -p knos/reader/books/my-book
   cp ~/Downloads/book.epub knos/reader/books/my-book/source.epub
   ```

2. Add to `config/content.yaml`:
   ```yaml
   materials:
     my-book:
       title: "Book Title"
       author: "Author Name"
       source: "knos/reader/books/my-book/source.epub"
   ```

3. Verify:
   ```bash
   uv run knos read list
   ```

### Adding Your Own PDF

PDFs require manual chapter page ranges. See [Usage Guide — Adding a PDF](USAGE.md#adding-a-pdf-with-chapters) for the full workflow.

For external textbooks with detailed chapter definitions, see `config/content.yaml.example.external`.

## The Reader-to-Drill Workflow

The Reader generates drill cards from your dialogue. Here's how they flow into the drill system:

```
1. Read & Discuss
   └── Press Ctrl+G during a session to generate cards

2. Review Drafts
   └── Cards saved to knos/reader/drafts/<material>/<chapter>/
   └── Edit for accuracy and clarity

3. Promote to Drill Queue
   └── Move reviewed cards to solutions/focus/<any-folder>/

4. Drill
   └── Run: uv run knos drill
   └── Cards appear when due according to Leitner scheduling
```

### Card Locations

| Location | Purpose |
|----------|---------|
| `knos/reader/drafts/` | Generated cards awaiting your review |
| `solutions/focus/` | Active cards in the drill queue |
| `solutions/examples/` | Reference examples (not drilled) |

## Privacy & API Costs

### What's Stored Locally

- Dialogue transcripts: `knos/reader/sessions/`
- Drill card state: `plan/schedule.json`
- All configuration files

### What's Sent to Google

When using the Reader, your messages and the text content you're reading are sent to Google's Gemini API. Review [Google's AI privacy policy](https://ai.google.dev/terms) for details.

**Recommendations:**
- Avoid uploading sensitive or proprietary content
- Use public domain texts when possible
- The bundled classics are all public domain

### API Costs

- Google Gemini offers a free tier (1500 requests/day)
- Typical self-study session: 20-50 exchanges
- Heavy users may exceed the free tier; check [Google AI pricing](https://ai.google.dev/pricing)

### Offline Use

- **Drill system**: Works completely offline
- **Reader**: Requires internet (LLM API calls)
- **Voice/TTS**: Works offline after model download

## Next Steps

- [Usage Guide](USAGE.md) — Command reference, workflows, keybindings
- [Pedagogy](PEDAGOGY.md) — The learning science behind the Reader
- [Card Format](../solutions/examples/README.md) — Creating drill cards
- [Troubleshooting](TROUBLESHOOTING.md) — Common issues and fixes
