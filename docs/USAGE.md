# Usage Guide

Operational reference for Knowledge OS. For first-time setup, see [Getting Started](GETTING_STARTED.md).

---

## Commands

All commands use the `uv run knos` prefix.

### Primary Commands

| Command | Description |
|---------|-------------|
| `uv run knos` | Launch TUI dashboard (default) |
| `uv run knos init` | Create config files interactively |
| `uv run knos read` | Launch Reader TUI |
| `uv run knos drill` | Launch Drill TUI |
| `uv run knos today` | Print CLI study summary |
| `uv run knos progress` | Generate PROGRESS.md report |

### Reader Subcommands

| Command | Description |
|---------|-------------|
| `uv run knos read list` | List registered materials |
| `uv run knos read info <id>` | Show material details and chapters |
| `uv run knos read clear <id> [ch]` | Clear session data |
| `uv run knos read export <id> [ch]` | Export session to markdown |
| `uv run knos read test` | Verify LLM configuration |

### JSON Output (for scripting)

| Command | Description |
|---------|-------------|
| `uv run knos read list --json` | Materials as JSON |
| `uv run knos read info <id> --json` | Material info as JSON |

---

## Data Locations

| Location | Contents | Gitignored? |
|----------|----------|-------------|
| `config/` | User configuration files | Yes (except `.example`) |
| `plan/schedule.json` | Drill card Leitner state | Yes |
| `plan/history.jsonl` | Drill session history | Yes |
| `solutions/focus/` | Active drill cards | Yes |
| `solutions/examples/` | Example cards (reference) | No |
| `knos/reader/sessions/` | Dialogue transcripts | Yes |
| `knos/reader/drafts/` | Generated cards awaiting review | Yes |
| `knos/reader/books/` | User-provided PDFs/EPUBs | Yes |
| `knos/reader/classics/` | Bundled classics | No |
| `knos/reader/articles/` | Bundled articles | No |

---

## Workflows

### Adding an EPUB (Recommended for New Users)

EPUBs are the easiest format—chapter structure is extracted automatically from the table of contents.

1. **Create directory and copy file:**
   ```bash
   mkdir -p knos/reader/books/my-book
   cp ~/Downloads/book.epub knos/reader/books/my-book/source.epub
   ```

2. **Add to `config/content.yaml`:**
   ```yaml
   materials:
     my-book:
       title: "Book Title"
       author: "Author Name"
       source: "knos/reader/books/my-book/source.epub"
   ```

3. **Verify:**
   ```bash
   uv run knos read list
   ```

### Adding a PDF with Chapters

PDFs require manual chapter page ranges because they lack structural metadata.

1. **Create directory and copy file:**
   ```bash
   mkdir -p knos/reader/books/my-textbook
   cp ~/Downloads/textbook.pdf knos/reader/books/my-textbook/source.pdf
   ```

2. **Find chapter page ranges:**
   - Open the PDF in any viewer
   - Navigate to each chapter using bookmarks or the table of contents
   - Note the PDF page number (shown at the bottom of the viewer)
   - Page numbers are 1-indexed and refer to PDF pages, not printed book pages

3. **Add to `config/content.yaml`:**
   ```yaml
   materials:
     my-textbook:
       title: "Textbook Title"
       author: "Author Name"
       source: "knos/reader/books/my-textbook/source.pdf"
       structure:
         type: chapters
         chapters:
           - { num: 1, title: "Introduction", pages: [15, 42] }
           - { num: 2, title: "Chapter Two", pages: [43, 78] }
           - { num: 3, title: "Chapter Three", pages: [79, 120] }
   ```

4. **Verify:**
   ```bash
   uv run knos read info my-textbook
   ```

For complete examples with OpenStax textbooks, see `config/content.yaml.example.external`.

### Adding an Article (Single-Unit PDF)

Articles skip chapter selection and open directly into dialogue.

1. **Copy to articles directory:**
   ```bash
   cp ~/Downloads/paper.pdf knos/reader/articles/my-paper.pdf
   ```

2. **Add to `config/content.yaml`:**
   ```yaml
   materials:
     my-paper:
       title: "Paper Title"
       author: "Author et al."
       source: "knos/reader/articles/my-paper.pdf"
       structure:
         type: article
   ```

### Reader to Drill Workflow

1. **Generate cards during a Reader session:**
   - Press `Ctrl+G` to generate drill cards from the dialogue
   - The LLM identifies concepts worth retaining

2. **Review drafts:**
   - Cards are saved to `knos/reader/drafts/<material>/<chapter>/`
   - Edit for accuracy and clarity
   - Delete cards that aren't useful

3. **Promote to drill queue:**
   - Move reviewed cards to `solutions/focus/<any-folder>/`
   - Create subdirectories to organize by topic if desired

4. **Drill:**
   ```bash
   uv run knos drill
   ```
   Cards appear when due according to Leitner scheduling.

---

## Drill Card Formats

### Code Blocks (Exact Reproduction)

For algorithms, formulas, and code you need to reproduce exactly:

```markdown
# Binary Search

## How It Works

Divide and conquer on a sorted array.

## Implementation

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```
```

Every fenced code block is a drill target. Content is revealed line-by-line during drill.

**Scoring:** 100% accuracy required to advance to the next Leitner box.

### Slots Blocks (Conceptual Knowledge)

For definitions, distinctions, and multi-part concepts:

```markdown
# Aristotle's Four Causes

## Overview

Aristotle's framework for explaining why things are as they are.

## The Four Causes

```slots
Material cause :: What something is made of
Formal cause :: The pattern or essence
Efficient cause :: The agent that brings it about
Final cause :: The purpose or end
```
```

**Format:** Each drillable line uses `Prompt :: Answer`. The prompt is shown; the answer is hidden.

**Scoring:** 80% accuracy required to advance.

**When to use each:**
- **Code blocks:** Executable code, algorithms, formulas, proofs—anything you need to reproduce exactly
- **Slots blocks:** Definitions, distinctions, processes, conceptual relationships

See [solutions/examples/README.md](../solutions/examples/README.md) for the complete format guide.

### Excluding Blocks from Drill

Prefix a block with `<!-- INFO -->` to make it informational only:

```markdown
<!-- INFO -->
```python
# This block is displayed but not drilled
```
```

---

## Dialogue Modes

Switch modes with `Ctrl+M` during a Reader session.

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **Socratic** | Probing questions, rarely gives answers | Default mode; builds understanding through questioning |
| **Clarify** | Direct explanations | When genuinely stuck; get unstuck, then return to Socratic |
| **Challenge** | Devil's advocate, stress-tests claims | When confident; tests robustness of understanding |
| **Teach** | You explain to a "confused student" | Reveals gaps; forces articulation |
| **Quiz** | Rapid-fire recall check | Retrieval practice for memory strengthening |
| **Technical** | Step-by-step guidance | Math, code, or procedural content |

**Review mode** is available via the Study Tools menu (not `Ctrl+M`) for cross-chapter synthesis.

See [PEDAGOGY.md](PEDAGOGY.md) for background on the design thinking behind each mode.

---

## Keybindings

### Reader TUI

| Key | Action |
|-----|--------|
| `Ctrl+M` | Switch dialogue mode |
| `Ctrl+G` | Generate drill cards |
| `Ctrl+R` | Voice input (requires voice extra) |
| `Ctrl+T` | Toggle TTS (requires voice extra) |
| `Enter` | Send message |
| `Esc` | Back / Cancel |

### Drill TUI

| Key | Action |
|-----|--------|
| `Enter` | Reveal next line / Advance |
| `y` | Mark answer correct |
| `n` | Mark answer incorrect |
| `q` | Quit drill session |
| `Esc` | Back |

### Dashboard TUI

| Key | Action |
|-----|--------|
| `d` | Start drill session |
| `r` | Open Reader |
| `q` | Quit |

---

## Configuration Reference

### reader.yaml

```yaml
llm:
  provider: "gemini"
  gemini:
    api_key: "YOUR_API_KEY"     # Or use api_key_env: "GOOGLE_API_KEY"
    model: "gemini-2.5-flash"   # Or gemini-3-flash-preview, gemini-3-pro-preview

voice:                          # Optional, requires --extra voice
  enabled: true
  model: "base"                 # tiny, base, small, medium, large-v3
  language: "en"

tts:                            # Optional, requires --extra voice or chatterbox
  enabled: true
  backend: "kokoro"             # kokoro (~1GB VRAM) or chatterbox (~3-4GB VRAM)
```

### content.yaml

See `config/content.yaml.example` (bundled content) and `config/content.yaml.example.external` (external content with examples).

**Material types:**
- EPUB: No structure block needed (auto-extracted)
- PDF with chapters: Requires `structure.type: chapters` with chapter list
- Article: Requires `structure.type: article`

### study.yaml

Optional configuration for domain rotation and study phases. See `config/study.yaml.example`.

---

## Leitner Box Intervals

The drill system uses Leitner spaced repetition:

| Box | Interval |
|-----|----------|
| 0 | 1 hour |
| 1 | 4 hours |
| 2 | 1 day |
| 3 | 3 days |
| 4 | 7 days |
| 5 | 14 days |
| 6 | 30 days |
| 7 | 90 days |

**Advancement:** 100% accuracy for code blocks, 80% for slots blocks.
**Reset:** Any mistake resets the card to box 0.

---

## Further Reading

- [Getting Started](GETTING_STARTED.md) — Installation and first session
- [Pedagogy](PEDAGOGY.md) — Design notes on LLM-assisted learning
- [Troubleshooting](TROUBLESHOOTING.md) — Common issues and fixes
- [Card Format](../solutions/examples/README.md) — Complete drill card specification
- [Reader Overview](../knos/reader/OVERVIEW.md) — Reader module details
