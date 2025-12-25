# Reader Module Overview

A reading companion that brings St. John's College seminar pedagogy to self-study.

---

## The St. John's College Tradition

This module draws explicitly from the pedagogy of [St. John's College](https://www.sjc.edu/) (Annapolis and Santa Fe)—a Great Books program where students spend four years reading primary sources from Homer to Einstein, engaging with them through seminar discussion rather than lecture.

Key aspects of this tradition that inform the Reader:

**Tutors, not professors.** Faculty at St. John's are called "tutors" and position themselves as fellow travelers in understanding, not authorities delivering interpretations. They have expertise, but within seminar they inquire alongside students.

**The text is the authority.** When disagreements arise, the resolution is "let's look at what the text says"—not "here's what scholars think" or "here's the right answer." The author's words are primary.

**Collaborative inquiry.** This is not adversarial cross-examination. The goal is shared understanding. When material is technical, those with relevant expertise help bring everyone to a common level so exploration can continue together.

**The opening question.** Seminars traditionally begin with a tutor posing a genuine question about the reading—not rhetorical, not leading, but an authentic point of entry into the text.

---

## How It Works

The Reader pairs you with an LLM tutor for dialogue about the material you're reading. The tutor has access to the full chapter, enabling discussion grounded in the actual text.

When you begin a new chapter, the tutor opens with a question about the reading. From there, you drive the conversation—ask questions, work through difficult passages, test your understanding.

### Dialogue Modes

| Mode | Behavior |
|------|----------|
| **Socratic** | Probing questions, rarely gives answers (default) |
| **Clarify** | Direct explanations when stuck |
| **Challenge** | Devil's advocate, stress-tests claims |
| **Teach** | You explain to a "confused student" |
| **Quiz** | Rapid-fire recall check |
| **Technical** | Step-by-step guidance through formulas and procedures |
| **Review** | Cross-chapter synthesis (only available via Study Tools menu) |

Switch modes with `Ctrl+M` during a session.

### Study Tools

The chapter selection screen includes a Study Tools section with special modes:

| Tool | Access | Behavior |
|------|--------|----------|
| **Review All Discussions** | Appears when sessions exist | Opens dialogue with all chapter transcripts as context. Helps synthesize learning, identify gaps, and create summaries across the entire book. |
| **Quiz Mode** | Always available | Select any chapter for rapid-fire recall testing. Each quiz is a fresh session (never resumes)—take as many quizzes as you like. |
| **Browse Quiz History** | Appears when quizzes exist | View past quiz sessions with full transcript viewer. |

**Quiz sessions** are timestamped uniquely (e.g., `quiz_ch01_20251224T143022`) so you can quiz the same chapter multiple times and compare performance across attempts.

### Card Generation

Press `Ctrl+G` to generate drill cards from the conversation. The LLM reviews the dialogue to identify concepts worth retaining—what you struggled with, what required clarification, what you explored deeply.

Cards go to `reader/drafts/` for review before entering the drill system.

---

## Setup

For complete setup instructions, see [docs/GETTING_STARTED.md](../../docs/GETTING_STARTED.md).

**Quick start:**

```bash
uv run knos init            # Create config files (prompts for API key)
uv run knos read test       # Verify LLM configuration
uv run knos read            # Start the Reader
```

Three bundled classics and five foundational articles work immediately after setup.

### Adding Your Own Materials

**EPUBs** are easiest—chapter structure is extracted automatically:

```yaml
materials:
  my-book:
    title: "Book Title"
    author: "Author Name"
    source: "knos/reader/books/my-book/source.epub"
```

**PDFs** require chapter page ranges. See [docs/USAGE.md](../../docs/USAGE.md#adding-a-pdf-with-chapters) for the full workflow.

---

## Keybindings

| Key | Action |
|-----|--------|
| `Ctrl+M` | Switch dialogue mode |
| `Ctrl+G` | Generate drill cards |
| `Ctrl+R` | Voice input |
| `Ctrl+T` | Toggle TTS |
| `Esc` | Back |

---

## File Structure

```
config/
  reader.yaml              # LLM API keys (gitignored)
  content.yaml             # Registered materials (gitignored)

knos/reader/
  sessions/<material-id>/  # Dialogue transcripts (gitignored)
    ch01.jsonl             #   Regular chapter sessions (append-only)
    ch01.meta.json         #   Session metadata (exchange count, tokens, etc.)
    review.jsonl           #   Review session for the material
    quiz_ch01_*.jsonl      #   Quiz sessions (timestamped, never overwritten)
  drafts/                  # Generated cards awaiting review
  prompts/                 # Dialogue mode prompts (socratic.md, quiz.md, review.md, etc.)
  classics/                # Bundled classics (Aristotle, Cervantes, Dostoevsky)
  books/                   # User-provided PDFs/EPUBs (gitignored)
```
