# Knowledge OS Roadmap

A roadmap for the TUI-based study system, documenting current capabilities and future enhancement ideas.

**Last updated**: 2025-12-19

> **Note:** This system was designed for PhD-level self-study across multiple domains. The examples reference specific textbooks (Tao, CLRS, etc.) as illustration—adapt to your own curriculum.

---

## Current State

### Study TUI (`./study`)

The **Textual-based TUI** is fully implemented as the primary entry point:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ./study (TUI Entry Point)                    │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard    │  Drill Screen  │  Browse Screen  │  Stats      │
│  ✅ Today     │  ✅ Line reveal│  ✅ Navigate    │  ⚪ Planned │
│  ✅ Progress  │  ✅ y/n scoring│  ✅ Categories  │             │
│  ✅ Due cards │  ✅ Blocks     │                 │             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    reviewer/core.py (Library)                   │
│  - Schedule management    - Markdown parsing                    │
│  - Leitner box logic      - Progress tracking                   │
│  - History logging        - Domain rotation                     │
└─────────────────────────────────────────────────────────────────┘
```

**Implemented (✅):**
- Unified dashboard with TodayPanel, ProgressPanel, StatusPanel, DrillListPanel
- Line-by-line reveal drilling with RevealBlock widgets
- Browse screen for solution navigation
- Keyboard-first navigation (vim-style: j/k, Enter, Esc)
- `schedule.json` persistence with Leitner box progression
- CLI fallbacks (`./study --today`, `./study --progress`)
- Progress report generation

### Reader Module (`./read`)

The **LLM-powered reading companion** provides structured dialogue with textbook content:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ./read (Reader TUI)                         │
├─────────────────────────────────────────────────────────────────┤
│  Select Material → Select Chapter → Dialogue Screen             │
│  ✅ Registry     │  ✅ Progress   │  ✅ Multi-mode dialogue     │
│  ✅ Extraction   │  ✅ Sessions   │  ✅ Card generation         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Reader Components                          │
│  reader/llm.py      — Gemini & Anthropic providers              │
│  reader/content.py  — PDF extraction, chapter loading           │
│  reader/prompts/    — Dialogue mode templates                   │
│  reader/session.py  — Session persistence & history             │
│  reader/voice.py    — Voice input (Whisper)                     │
│  reader/tts.py      — Text-to-speech output                     │
└─────────────────────────────────────────────────────────────────┘
```

**Implemented (✅):**
- Material registry (`content_registry.yaml`) with chapter/page mappings
- PDF → Markdown extraction (`./read --extract <material-id>`)
- Five dialogue modes: Socratic, Clarify, Challenge, Teach, Quiz
- LLM providers: Google Gemini (with context caching), Anthropic Claude
- Session persistence with transcript history
- Card generation from dialogue sessions → `reader/drafts/`
- Voice input via Whisper (local or API)
- Text-to-speech for LLM responses
- Jinja2 prompt templates for each dialogue mode

---

## Roadmap: TUI Enhancements

### Tier 1: High Value, Low Effort

#### 1.1 Streak Tracking
**Status:** Not started | **Effort:** Low

Display consecutive study days in the dashboard.

```
🔥 Streak: 12 days (best: 34)
```

**Implementation:**
- Parse `schedule.json` for `last_reviewed` dates
- Add streak calculation to `core.py`
- Display in `StatusPanel`

#### 1.2 Difficulty Calibration
**Status:** Not started | **Effort:** Low

Track `reset_count` for each card. Cards that repeatedly fall to box 0 indicate weak spots.

**Implementation:**
- Add `reset_count` field to schedule entries
- Increment on box reset (score < threshold)
- Surface "Hardest cards" in a new panel or stats view
- Flag cards with >3 resets for attention

#### 1.3 Post-Drill Reflection
**Status:** Not started | **Effort:** Low-Medium

After completing a card, prompt for metacognitive reflection:
- Which proof technique did you use? (Direct, Contradiction, Induction, ε-δ, etc.)
- What was the key insight?

**Implementation:**
- Add optional reflection modal after DrillScreen completion
- Store technique tags in `schedule.json` or `history.jsonl`
- Surface weak techniques in summary view

---

### Tier 2: High Value, Medium Effort

#### 2.1 Stats Screen
**Status:** Planned | **Effort:** Medium

A dedicated screen for visualizing progress:
- Cards by box distribution (histogram)
- Review history over time
- Domain coverage breakdown
- Weak technique identification

**Implementation:**
- New `StatsScreen` in `tui/screens/stats.py`
- Rich-based charts (bar graphs via box-drawing characters)
- Parse `history.jsonl` for temporal data

#### 2.2 LLM Help Integration
**Status:** Not started | **Effort:** Medium

When stuck during drill, press `h` to get a Socratic hint (not the answer).

**Implementation:**
- Keybind `h` in DrillScreen → "Get Hint"
- Send current block context + card metadata to Gemini API
- Display hint in modal (one guiding question only)
- Track hint usage in history

**Prompt template:**
```
You are a Socratic tutor. The student is trying to recall:
[BLOCK CONTENT - first 2 lines revealed]

They are stuck. Ask ONE guiding question that points toward the key insight.
Do NOT reveal the answer.
```

#### 2.3 Context-Aware Prompt Copier
**Status:** Not started | **Effort:** Medium

Press `?` anywhere to get a context-appropriate LLM prompt copied to clipboard.

**Examples:**
- On Dashboard → Weekly synthesis prompt with this week's domains
- On DrillScreen → Socratic proof guide with current theorem
- On BrowseScreen → Proof technique identifier for selected card

**Implementation:**
- `pyperclip` for clipboard access
- Prompt templates in `reviewer/prompts/` or inline
- Context injection based on current screen state

#### 2.4 Search Across Solutions
**Status:** Not started | **Effort:** Medium

Full-text search across all solution files from Browse screen.

**Implementation:**
- Search input widget in BrowseScreen
- Filter/highlight matching cards
- Jump to card on selection

---

### Tier 3: High Value, Higher Effort

#### 3.1 PDF → Markdown Pipeline
**Status:** ✅ Implemented (Reader module)

Extract textbook chapters as markdown via the Reader:

```bash
./read --extract <material-id>
# Output: reader/extracted/<material-id>/ch01.md, ch02.md, ...
```

Materials are registered in `reader/content_registry.yaml` with chapter-to-page mappings. Extraction uses `pymupdf`.

#### 3.2 LLM-Assisted Card Generation
**Status:** ✅ Implemented (Reader module)

Generate drill cards from Reader dialogue sessions:

1. Start a reading session: `./read`
2. Dialogue with the material (Socratic, Challenge, etc.)
3. Press `g` to generate cards from session insights
4. Cards saved to `reader/drafts/` for review
5. Move approved cards to `solutions/focus/`

Uses Jinja2 prompt templates in `reader/prompts/card_generation.md`.

#### 3.3 Adaptive Quiz Mode
**Status:** Not started | **Effort:** High

Interactive quiz that adapts difficulty based on performance.

```
./study quiz --domain analysis --chapter "Tao Ch. 6"
```

**Flow:**
1. Start with definition recall
2. Correct → theorem statement
3. Correct → proof technique
4. Correct → "what fails if we drop hypothesis X"
5. Wrong → hint + retry

**TUI Integration:**
- New QuizScreen
- Progress through difficulty tiers
- Summary at end with weak spots identified

---

## Roadmap: Content & Workflow

### Domain Templates
**Status:** Not started | **Effort:** Low

Skeleton templates for manual card creation:

```
solutions/templates/
├── analysis.md      # Statement, Proof technique, Key insight
├── algorithms.md    # Invariant, Complexity, Implementation
├── micro.md         # Assumptions, Result, Intuition
└── ml.md            # Model, Key equations, Computational notes
```

**TUI Integration:**
- "New Card" action → select template → open in $EDITOR
- Template pre-fills frontmatter and section headers

### Connection Cards
**Status:** Not started | **Effort:** Low

Cross-domain synthesis cards linking concepts:

```
solutions/cross_domain/
├── compactness_equilibrium.md      # Analysis ↔ Micro
├── bellman_contraction.md          # Algorithms ↔ ML
├── continuity_preferences.md       # Analysis ↔ Micro
└── complexity_equilibria.md        # Algorithms ↔ Micro
```

**Format:**
````markdown
# Connection: [Title]

## Domain A: [Concept]
Brief definition and context.

## Domain B: [Concept]
Brief definition and context.

## The Connection
How are they structurally related?

## Guiding Question
<!-- TARGET -->
```[proof]
What mathematical structure appears in both contexts?
Why does the same technique work?
```
<!-- /TARGET -->
````

### Lean Integration
**Status:** Blocked | **Effort:** High

Verify recalled Lean proofs by running `lake build`.

**Prerequisite:** Lean 4 environment setup complete

**TUI Integration:**
- Detect `.lean` code blocks
- "Verify" action sends to Lean compiler
- Display success/error inline

---

## LLM Prompt Library

A collection of copy-paste prompts for use alongside the TUI workflow is available in **[docs/prompts.md](../prompts.md)**.

Includes prompts for:
- Socratic proof guidance
- Proof technique identification
- Domain-specific tutoring
- Cross-domain synthesis
- Metacognitive reflection
- Card generation

---

## Implementation Priority

Recommended sequence for remaining features:

### Completed
- ✅ PDF extraction pipeline (Reader module)
- ✅ LLM-assisted card generation (Reader module)
- ✅ Multi-provider LLM integration (Gemini, Anthropic)

### Phase A: Quick Wins
1. Streak tracking in StatusPanel
2. Difficulty calibration (`reset_count`)
3. Search in Browse screen

### Phase B: Core Enhancements
4. Stats screen with history visualization
5. Post-drill reflection modal
6. LLM hint integration in drill mode

### Phase C: Future Consideration
7. Adaptive quiz mode
8. Lean integration (when environment ready)
9. Context-aware prompt copier

---

## Appendix: Learning Science Principles

These features are designed around five learning science principles:

| Principle | How the system supports it |
|-----------|---------------------------|
| **Active recall** | Line-by-line reveal forces retrieval before seeing answer |
| **Spaced repetition** | Leitner box scheduling optimizes review intervals |
| **Metacognition** | Reflection prompts; technique tagging |
| **Desirable difficulty** | Difficulty calibration surfaces weak spots |
| **Interleaving** | Domain rotation; cross-domain connection cards |
