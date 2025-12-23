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

Switch modes with `Ctrl+M` during a session.

### Card Generation

Press `Ctrl+G` to generate drill cards from the conversation. The LLM reviews the dialogue to identify concepts worth retaining—what you struggled with, what required clarification, what you explored deeply.

Cards go to `reader/drafts/` for review before entering the drill system.

---

## Setup

Run `uv run knos init` to create config files interactively, or copy them manually.

### LLM Configuration (`config/reader.yaml`)

```bash
cp config/reader.yaml.example config/reader.yaml
```

Edit with your Gemini API key.

### Registering Materials (`config/content.yaml`)

```bash
cp config/content.yaml.example config/content.yaml
```

Add entries for your PDFs with chapter page ranges:

```yaml
materials:
  my-textbook:
    title: "Introduction to Subject"
    author: "Author Name"
    source: "knos/reader/sources/my-textbook/source.pdf"
    structure:
      type: chapters
      chapters:
        - { num: 1, title: "Chapter One", pages: [10, 45] }
        - { num: 2, title: "Chapter Two", pages: [46, 89] }
```

Place the PDF at `knos/reader/sources/<material-id>/source.pdf`.

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
  sessions/                # Dialogue transcripts (gitignored)
  drafts/                  # Generated cards awaiting review
  prompts/                 # Dialogue mode prompts
  classics/                # Bundled classics (Aristotle, Cervantes, Dostoevsky)
  sources/                 # User-provided PDFs/EPUBs (gitignored)
```
