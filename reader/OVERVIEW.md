# Reader Module Overview

A seminar-style reading companion that brings St. John's College pedagogy to self-study through structured LLM dialogue.

---

## Vision

The **reader** module fills the gap between passive reading and active drilling. In the St. John's model, understanding emerges through *dialogue*—articulating ideas, defending interpretations, and responding to challenges. The reader creates this experience with an LLM as seminar partner.

```
Current Knowledge OS Pipeline:
  Read (passive) ──────────────────────► Drill (retention)
                        ↑
                   GAP: where does
                   understanding happen?

With Reader:
  Read ───► Reader (dialogue/understanding) ───► Card Creation ───► Drill
```

The LLM reads the material alongside you, enabling substantive dialogue grounded in the actual text—not just general knowledge.

---

## Core Concepts

### Seminar-Style Dialogue

The reader doesn't answer questions—it asks them. When you claim to understand something, it probes. When you accept an argument too easily, it challenges. This creates the accountability that makes seminars effective.

### Material Context

The LLM has access to the chapter/section you're reading. This enables:
- Questions about specific passages
- Challenges grounded in what the author actually wrote
- Connections across sections of the same text

### Structured Sessions

Each reading session follows phases inspired by seminar preparation:

1. **Pre-Reading** — Orient to the material
   - What do you already know about this topic?
   - What questions are you bringing?
   - What do you expect to learn?

2. **Active Dialogue** — Engage with the text
   - Work through the material with the LLM
   - Switch modes as needed (Socratic, Clarify, Challenge)
   - Capture insights for later card creation

3. **Synthesis** — Consolidate understanding
   - What were the key insights?
   - How does this connect to prior knowledge?
   - What's still unclear?
   - Generate candidate drill cards

### Dialogue Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Socratic** | Probing questions, rarely gives answers | Default—forces articulation |
| **Clarify** | Direct explanations and answers | When genuinely stuck |
| **Challenge** | Devil's advocate, attacks claims | Testing robustness |
| **Teach** | Plays confused student | Forces clear explanation |
| **Quiz** | Rapid-fire recall questions | Pre-card-creation check |

---

## User Flow

### Launch

```bash
$ ./reader
```

### Material Selection

```
┌─────────────────────────────────────────────────────────┐
│  READER                                    [?] Help     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Select Material:                                       │
│                                                         │
│  ▸ Build a Large Language Model (From Scratch)          │
│    How to Prove It (Velleman)                           │
│    Analysis I (Tao)                                     │
│    PML: An Introduction (Murphy)                        │
│    Microeconomic Foundations I (Kreps)                  │
│                                                         │
│  [Enter] Select  [/] Search  [q] Quit                   │
└─────────────────────────────────────────────────────────┘
```

Materials populated from `content_registry.yaml` (explicit registration required).

### Chapter Selection

```
┌─────────────────────────────────────────────────────────┐
│  How to Prove It (Velleman)                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Chapters:                                              │
│                                                         │
│    Introduction                                 ○       │
│  ▸ Ch 1: Sentential Logic                       ◐       │
│      1.1 Deductive Reasoning and Connectives    ●       │
│      1.2 Truth Tables                           ●       │
│      1.3 Variables and Sets                     ◐       │
│      1.4 Operations on Sets                     ○       │
│      1.5 Conditional and Biconditional          ○       │
│    Ch 2: Quantificational Logic                 ○       │
│    ...                                                  │
│                                                         │
│  ○ Not started  ◐ In progress  ● Discussed              │
│                                                         │
│  [Enter] Start session  [r] Resume  [h] History         │
└─────────────────────────────────────────────────────────┘
```

### Dialogue Interface

```
┌─────────────────────────────────────────────────────────┐
│  1.3 Variables and Sets              [Mode: Socratic]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ READER: You're beginning section 1.3 on         │    │
│  │ variables and sets. Before we dive in:          │    │
│  │                                                 │    │
│  │ 1. What's your current understanding of what    │    │
│  │    a set is?                                    │    │
│  │ 2. Have you encountered set-builder notation    │    │
│  │    before?                                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ YOU: A set is a collection of objects. I've     │    │
│  │ seen {x : P(x)} notation but not sure about     │    │
│  │ when it's valid—Russell's paradox?              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ READER: Good instinct to worry about Russell.   │    │
│  │ As you read, Velleman addresses this on p.27.   │    │
│  │ Pay attention to his treatment of "universes    │    │
│  │ of discourse." Why might restricting the        │    │
│  │ domain of set-builder notation help?            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ > _                                      [🎤 Voice: On] │
│                                                         │
│ [Enter] Send  [Ctrl+M] Mode  [Ctrl+C] Capture           │
│ [Ctrl+S] Synthesize  [Ctrl+V] Voice toggle  [Ctrl+Q]    │
└─────────────────────────────────────────────────────────┘
```

### Synthesis Phase

```
┌─────────────────────────────────────────────────────────┐
│  Session Synthesis: 1.3 Variables and Sets              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Duration: 47 minutes                                   │
│  Exchanges: 23                                          │
│                                                         │
│  Captured Insights (4):                                 │
│                                                         │
│  1. "Universe of discourse restricts set-builder to     │
│      avoid Russell's paradox—can only form subsets      │
│      of existing sets"                                  │
│                                                         │
│  2. "Free vs bound variables: free variables make       │
│      expressions into predicates, not statements"       │
│                                                         │
│  3. "Truth set of P(x) = {x ∈ U : P(x)} — the set      │
│      of all elements satisfying the predicate"          │
│                                                         │
│  4. "Empty set subtlety: ∀x ∈ ∅, P(x) is vacuously     │
│      true for any P"                                    │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Generate drill cards from insights?                    │
│                                                         │
│  [g] Generate cards  [e] Edit insights  [s] Save only   │
└─────────────────────────────────────────────────────────┘
```

---

## Content Parsing

### Supported Formats

| Format | Parser | Notes |
|--------|--------|-------|
| **PDF** | `pymupdf` or `pdfplumber` | Extract text, preserve structure |
| **Markdown** | Native | Already in correct format |
| **EPUB** | `ebooklib` | Extract chapters, convert to markdown |

### Content Organization

Content sources are explicitly mapped in a registry. **No auto-discovery**—materials must be registered to appear in the reader.

```
reader/
  content_registry.yaml   # Material definitions (explicit only)
  extracted/              # Centralized extraction output
    how-to-prove-it/
      ch01.md
      ch02.md
      ...
    build-llm-from-scratch/
      ch01.md
      ch02.md
      ...
```

```yaml
# content_registry.yaml

materials:
  how-to-prove-it:
    title: "How to Prove It: A Structured Approach"
    author: "Daniel J. Velleman"
    source: "Textbooks/HTPI/How to Prove it - A Structured Approach.pdf"
    structure:
      type: "chapters"
      chapters:
        - { num: 1, title: "Sentential Logic", pages: [8, 57] }
        - { num: 2, title: "Quantificational Logic", pages: [58, 95] }
        # ...

  build-llm-from-scratch:
    title: "Build a Large Language Model (From Scratch)"
    author: "Sebastian Raschka"
    source: "extra/Build_a_Large_Language_Model_(From_Scrat.pdf"
    structure:
      type: "chapters"
      chapters:
        - { num: 1, title: "Understanding Large Language Models", pages: [1, 30] }
        - { num: 2, title: "Working with Text Data", pages: [31, 72] }
        # ...

  analysis-i:
    title: "Analysis I"
    author: "Terence Tao"
    source: "Textbooks/Tao/Analysis I _ Fourth Edition -- Terence Tao.pdf"
    structure:
      type: "chapters"
      chapters:
        - { num: 1, title: "Introduction", pages: [1, 10] }
        # ...
```

### Managing the Content Registry

The registry is the single source of truth for available materials. To add or remove materials:

**Adding a new material:**

1. Add entry to `content_registry.yaml` with:
   - `title`, `author`, `source` (path to PDF/EPUB/Markdown)
   - `structure.chapters` with explicit page ranges
2. Run extraction: `./reader --extract <material-id>`
3. Verify extracted chapters in `reader/extracted/<material-id>/`

**Removing a material:**

1. Delete entry from `content_registry.yaml`
2. Optionally remove `reader/extracted/<material-id>/` directory
3. Sessions in `reader/sessions/<material-id>/` are preserved (manual cleanup if desired)

**Updating chapter boundaries:**

1. Edit `structure.chapters` in registry
2. Re-run extraction: `./reader --extract <material-id>`

### Text Extraction Pipeline

Extraction is explicit via CLI command:

```bash
# Extract all chapters for a material
./reader --extract how-to-prove-it

# Output: reader/extracted/how-to-prove-it/ch01.md, ch02.md, ...
```

```python
# reader/content.py

def extract_material(material_id: str) -> None:
    """Extract all chapters from source to reader/extracted/."""
    registry = load_registry()
    material = registry[material_id]
    output_dir = Path("reader/extracted") / material_id
    output_dir.mkdir(parents=True, exist_ok=True)

    for chapter in material["structure"]["chapters"]:
        content = extract_pages(material["source"], chapter["pages"])
        output_path = output_dir / f"ch{chapter['num']:02d}.md"
        output_path.write_text(content)

def load_chapter(material_id: str, chapter_num: int) -> str:
    """Load pre-extracted chapter content."""
    path = Path("reader/extracted") / material_id / f"ch{chapter_num:02d}.md"
    if not path.exists():
        raise ValueError(f"Chapter not extracted. Run: ./reader --extract {material_id}")
    return path.read_text()
```

### Chapter Detection

Chapter boundaries are **explicitly defined** in the registry via page ranges. This is the most reliable approach for academic texts where chapter boundaries may not follow simple patterns.

For each material, you must specify the page range for each chapter. This is a one-time setup cost that ensures reliable extraction.

---

## LLM Integration

### Provider Configuration

The reader supports multiple LLM providers via a common interface:

```yaml
# reader/config.yaml (or in main config)

llm:
  provider: "anthropic"  # anthropic | openai | ollama | custom
  model: "claude-sonnet-4-20250514"

  # Provider-specific settings
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"  # or inline, but env preferred
    max_tokens: 4096

  openai:
    api_key_env: "OPENAI_API_KEY"
    model: "gpt-4o"

  ollama:
    host: "http://localhost:11434"
    model: "llama3"
```

### Provider Interface

```python
# reader/llm.py

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system: str) -> str:
        """Send messages, return response."""
        pass

class AnthropicProvider(LLMProvider):
    async def chat(self, messages, system):
        # Use anthropic SDK
        ...

class OpenAIProvider(LLMProvider):
    async def chat(self, messages, system):
        # Use openai SDK
        ...

def get_provider(config: dict) -> LLMProvider:
    """Factory for configured provider."""
    ...
```

### System Prompts

Stored as markdown templates:

```
reader/
  prompts/
    base.md          # Core seminar companion identity
    socratic.md      # Socratic mode additions
    clarify.md       # Clarify mode
    challenge.md     # Devil's advocate mode
    teach.md         # Confused student mode
    quiz.md          # Quiz mode
    pre_reading.md   # Pre-reading phase
    synthesis.md     # Synthesis phase
```

Example base prompt structure:

```markdown
# reader/prompts/base.md

You are a Socratic reading companion in the tradition of the St. John's College
seminar. Your role is to help the user achieve genuine understanding through
dialogue—not to lecture or provide answers.

## Current Context

**Material:** {{book_title}}
**Section:** {{chapter_title}}
**Phase:** {{session_phase}}

## The Text

The user is reading the following section:

<text>
{{chapter_content}}
</text>

## Prior Context

{{#if prior_sessions}}
Previous sessions on this material covered:
{{prior_session_summary}}
{{/if}}

{{#if captured_insights}}
Insights captured so far this session:
{{captured_insights}}
{{/if}}

## Your Role

1. **Ask, don't tell.** When the user claims understanding, probe it.
2. **Ground in the text.** Reference specific passages, page numbers, examples.
3. **Challenge assumptions.** If they accept something too easily, push back.
4. **Demand precision.** Vague language often hides vague thinking.
5. **Respect autonomy.** They lead; you sharpen.

## Anti-patterns

- Praising correct answers effusively
- Giving answers when questions would serve better
- Accepting "I think I understand" without verification
- Monologuing or lecturing
- Losing connection to the actual text
```

---

## Speech-to-Text

Voice input enables a more natural seminar flow—speaking rather than typing.

### Option A: OpenAI Whisper API

**Pros:**
- Highest accuracy, especially for technical/mathematical language
- No local resources required
- Handles accents and speech variations well
- Simple integration (audio in, text out)

**Cons:**
- Requires network connection
- Per-minute cost (~$0.006/min for whisper-1)
- Audio must be sent to external server (privacy consideration)
- Latency (upload + processing, typically 1-3s for short utterances)

**Integration:**
```python
import openai

def transcribe(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        return openai.audio.transcriptions.create(
            model="whisper-1",
            file=f
        ).text
```

### Option B: Local Whisper (whisper.cpp or faster-whisper)

**Pros:**
- Fully offline—works without network
- No per-use cost after setup
- Privacy—audio never leaves machine
- Lower latency for short utterances (no upload)

**Cons:**
- Model download required:
  - `tiny`: ~75MB, fastest, lower accuracy
  - `base`: ~150MB, good balance
  - `small`: ~500MB, better accuracy
  - `medium`: ~1.5GB, high accuracy
  - `large`: ~3GB, highest accuracy
- Uses local CPU/GPU resources during transcription
- Setup complexity (Python bindings, model management)
- Accuracy slightly lower than API for edge cases

**Integration (faster-whisper):**
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu")  # or "cuda"

def transcribe(audio_path: str) -> str:
    segments, _ = model.transcribe(audio_path)
    return " ".join(s.text for s in segments)
```

### Option C: Hybrid Approach

- Default to local Whisper for low-latency, offline operation
- Fall back to API when local transcription confidence is low
- User toggle to force one or the other

### Recommendation

For a self-study system where sessions may be long and network availability varies:

**Start with local Whisper (`base` model):**
- ~150MB download is reasonable
- Works offline
- Good enough accuracy for conversational input
- Can upgrade to `small` or `medium` if accuracy issues arise

Add Whisper API as optional upgrade for users who prefer it.

### Audio Capture

```python
# reader/voice.py

import sounddevice as sd
import numpy as np

class VoiceCapture:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_buffer = []

    def start_recording(self):
        self.recording = True
        self.audio_buffer = []
        # Start audio stream...

    def stop_recording(self) -> np.ndarray:
        self.recording = False
        return np.concatenate(self.audio_buffer)
```

### Voice UI

- **Activation**: Toggle on/off (not push-to-talk)
- **Feedback**: Simple "Recording..." text indicator
- **Keybinding**: `Ctrl+V` toggles voice mode

---

## Session Persistence

### File Structure

```
reader/
  sessions/
    how-to-prove-it/
      ch01-sentential-logic/
        2025-01-15T14-30-00.jsonl    # Dialogue transcript
        2025-01-15T14-30-00.meta.json # Session metadata
        insights.md                   # Accumulated insights
      ch02-quantificational-logic/
        ...
    build-llm-from-scratch/
      ...

  content_registry.yaml
  config.yaml
```

### Session Metadata

```json
{
  "material_id": "how-to-prove-it",
  "chapter": "1.3",
  "chapter_title": "Variables and Sets",
  "started": "2025-01-15T14:30:00Z",
  "ended": "2025-01-15T15:17:00Z",
  "duration_minutes": 47,
  "phase_completed": "synthesis",
  "exchanges": 23,
  "mode_distribution": {
    "socratic": 18,
    "clarify": 3,
    "challenge": 2
  },
  "insights_captured": 4,
  "cards_generated": 3
}
```

### Dialogue Transcript

```jsonl
{"role": "system", "phase": "pre_reading", "timestamp": "..."}
{"role": "assistant", "content": "You're beginning section 1.3...", "timestamp": "..."}
{"role": "user", "content": "A set is a collection...", "input_mode": "voice", "timestamp": "..."}
{"role": "assistant", "content": "Good instinct to worry about Russell...", "timestamp": "..."}
{"event": "mode_change", "from": "socratic", "to": "clarify", "timestamp": "..."}
{"event": "insight_captured", "content": "Universe of discourse restricts...", "timestamp": "..."}
```

### Resume Capability

When resuming an in-progress session:
1. Load transcript
2. Reconstruct conversation context for LLM
3. Summarize where we left off for user
4. Continue dialogue

---

## Integration Points

### With Syllabus

Materials list populated from `Syllabus-v2.md`:
- Parse syllabus for book titles
- Match to entries in `content_registry.yaml`
- Show reading progress alongside syllabus goals

### With Card Creation

Post-synthesis flow:
1. User selects insights to convert to cards
2. LLM drafts cards, adapting format to content type:
   - **Algorithm**: Time/Space → How It Works → Code blocks → When to Use
   - **Logic/Proof**: Source ref → Statement → Key Insight
   - **Tactic**: Use for → Syntax → Effect → Key Insight
   - **Definition**: Term → Formal definition → Examples
   - **Theorem**: Statement → Proof sketch → Key insight
3. Cards saved to `reader/drafts/` (flat structure, auto-generated filenames)
4. User manually reviews and moves approved cards to `solutions/`
5. Cards enter drill system independently

**Drafts location**: `reader/drafts/` (flat, not mirroring `solutions/` subdirectories)

```
reader/
  drafts/
    demorgan_laws.md
    bpe_algorithm.md
    induction_template.md
    ...
```

**Not** auto-queued—manual review workflow.

### With Drill System

No direct integration initially. The reader produces understanding; the drill system handles retention. They share the filesystem but operate independently.

Future consideration: Link cards back to reader sessions for context during drill failures.

---

## Architecture

### Project Integration

The `reader/` module is a **sibling to `reviewer/` and `tui/`** within the `knowledge/` repository. It shares:

- **Virtual environment**: The root `.venv/` managed by `uv`
- **Dependencies**: Added to root `pyproject.toml` (not a separate package)
- **Entry point pattern**: `./reader` executable at repo root, like `./study` and `./drill`

```
knowledge/                    # Repository root
  pyproject.toml              # Shared dependencies (add reader deps here)
  .venv/                      # Shared virtual environment (uv-managed)

  reviewer/                   # Existing: core library + CLI
  tui/                        # Existing: Textual TUI apps
  reader/                     # New: reading companion module

  ./study                     # Existing entry point
  ./drill                     # Existing entry point
  ./reader                    # New entry point (executable script)
```

### Reader Module Structure

```
reader/
  __init__.py
  app.py                  # Textual TUI entry point (ReaderApp)
  config.py               # Configuration loading
  content.py              # Content extraction and management
  llm.py                  # LLM provider abstraction
  session.py              # Session state and persistence
  voice.py                # Audio capture and STT
  prompts.py              # Prompt template loading/rendering

  screens/
    __init__.py
    select_material.py    # Material selection screen
    select_chapter.py     # Chapter selection screen
    dialogue.py           # Main dialogue interface
    synthesis.py          # Session synthesis screen

  prompts/
    base.md
    socratic.md
    clarify.md
    challenge.md
    teach.md
    quiz.md
    pre_reading.md
    synthesis.md

  extracted/              # Pre-extracted chapter content (gitignored, regenerate with --extract)
    how-to-prove-it/
    build-llm-from-scratch/
    ...

  drafts/                 # Generated cards awaiting manual review (flat)

  sessions/               # Session transcripts and metadata (gitignored)

  content_registry.yaml   # Material definitions (explicit registry)
  config.yaml             # Reader configuration (gitignored, contains API keys)
  config.yaml.example     # Template for config.yaml (tracked)
```

### Entry Point

```python
#!/usr/bin/env python3
# ./reader (executable at repo root)

from reader.app import ReaderApp

if __name__ == "__main__":
    app = ReaderApp()
    app.run()
```

---

## Dependencies

Dependencies are added to the **root `pyproject.toml`** (not a separate file). Install with `uv sync` from repo root.

```toml
# Add to knowledge/pyproject.toml [project.dependencies]

# Existing (already present)
# textual = ">=0.47.0"
# rich = ">=13.0.0"

# New for reader (Phase 1)
anthropic = ">=0.18.0"      # Claude API
httpx = ">=0.25.0"          # HTTP client for LLM APIs
pyyaml = ">=6.0"            # Config files
jinja2 = ">=3.0"            # Prompt templating
pymupdf = ">=1.23.0"        # PDF extraction

# Later phases
openai = ">=1.0.0"          # OpenAI API / Whisper (Phase 4-5)
ebooklib = ">=0.18"         # EPUB parsing (Phase 5)
sounddevice = ">=0.4.6"     # Audio capture (Phase 4)
faster-whisper = ">=0.9.0"  # Local STT (Phase 4)
numpy = ">=1.24.0"          # Audio processing (Phase 4)
```

Run `uv sync` after adding dependencies—the shared `.venv/` will be updated.

---

## Design Decisions

Summary of key design choices:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Context scope** | Full chapter | Current materials fit in context; no RAG needed |
| **Pre-extraction** | Explicit CLI command | `./reader --extract <material-id>` for control |
| **Extraction format** | Per-chapter .md files | Easy to load specific chapters |
| **Extraction location** | Centralized `reader/extracted/` | Clean separation from source files |
| **Session granularity** | Per-chapter | Sufficient granularity for most texts |
| **Content registry** | Explicit only | No auto-discovery; documented add/remove process |
| **Voice activation** | Toggle on/off | Simpler than push-to-talk |
| **Voice feedback** | "Recording..." text | Simple, no waveform complexity |
| **Card format** | Adapt to content type | Match existing `solutions/` patterns |
| **Card staging** | `reader/drafts/` (flat) | Manual review before moving to `solutions/` |
| **Card naming** | Auto-generated from content | No user prompting during synthesis |
| **Version control** | Shared repo, selective gitignore | `extracted/`, `sessions/`, `config.yaml` gitignored; code tracked |

---

## Implementation Phases

### Phase 1: Core Infrastructure

- [ ] Content registry schema and loading
- [ ] `./reader --extract <material-id>` CLI command
- [ ] PDF extraction to per-chapter .md files
- [ ] Single LLM provider (Anthropic)
- [ ] Basic prompt template system

### Phase 2: TUI & Dialogue

- [ ] TUI skeleton (material → chapter → dialogue flow)
- [ ] Basic dialogue with mode switching
- [ ] Session persistence (save/resume)
- [ ] Insight capture during dialogue

### Phase 3: Structured Sessions

- [ ] Pre-reading phase prompts
- [ ] Synthesis phase UI
- [ ] Card generation from insights (to `reader/drafts/`)
- [ ] Session history and progress tracking

### Phase 4: Voice Input

- [ ] Audio capture integration
- [ ] Local Whisper STT (base model)
- [ ] Voice toggle in dialogue UI
- [ ] "Recording..." indicator

### Phase 5: Polish

- [ ] Multiple LLM providers (OpenAI, Ollama)
- [ ] EPUB + Markdown support
- [ ] Whisper API as optional alternative

---

*Last updated: 2025-12-17*
