# Knowledge OS Roadmap

Current capabilities and future enhancement ideas for the TUI-based study system.

**Last updated**: 2025-12-20

---

## Current State

### Unified CLI (`knos`)

Single entry point for all functionality:

```
knos              Launch study TUI (default)
knos today        CLI dashboard
knos study        Launch study TUI
knos drill        Launch drill TUI
knos read         Launch reader TUI
knos progress     Generate PROGRESS.md

knos read list              List registered materials
knos read clear <id> [ch]   Clear session data
knos read test              Test LLM provider
```

### Study Dashboard

The Textual-based TUI provides a unified command center:

```
┌─────────────────────────────────────────────────────────────────┐
│                         knos (TUI)                              │
├─────────────────────────────────────────────────────────────────┤
│  TodayPanel     │  ProgressPanel  │  ReaderPanel               │
│  Domain + Task  │  Sprint bars    │  Materials + sessions      │
├─────────────────────────────────────────────────────────────────┤
│  StatusPanel (Box 0, Overdue, Due Now, Never Practiced)        │
├─────────────────────────────────────────────────────────────────┤
│  DrillListPanel (navigable queue with ↑↓, Enter to drill)      │
└─────────────────────────────────────────────────────────────────┘

Keybindings:
  d       Drill all cards
  Enter   Drill selected card
  r       Open Reader
  b       Browse solutions
  p       Progress report
  s       Syllabus/milestones
  ctrl+r  Refresh
```

**Implemented:**
- Dashboard with 5 panels (Today, Progress, Reader, Status, DrillList)
- Line-by-line reveal drilling with RevealBlock widgets
- Browse screen for solution navigation
- Keyboard-first navigation (vim-style: j/k, Enter, Esc)
- Reader integration (press `r` to push reader screens onto stack)
- `schedule.json` persistence with Leitner box progression
- Progress report generation

### Reader Module

LLM-powered reading companion with structured dialogue:

```
┌─────────────────────────────────────────────────────────────────┐
│  Select Material → Select Chapter → Dialogue Screen             │
├─────────────────────────────────────────────────────────────────┤
│  Dialogue Modes: Socratic, Clarify, Challenge, Teach, Quiz      │
│  LLM Provider:   Gemini (with caching)                          │
│  Voice:          Whisper input, TTS output                      │
└─────────────────────────────────────────────────────────────────┘
```

**Setup:**
1. Run `knos init` to create config files
2. Place PDF in `knos/reader/sources/<material-id>/source.pdf`
3. Register in `config/content.yaml` with chapter page ranges
4. Run `knos read`

Text is extracted on-demand from PDF page ranges during reading sessions.

**Implemented:**
- Material registry with chapter/page mappings
- Five dialogue modes with Jinja2 prompt templates
- Session persistence with transcript history
- Card generation from sessions → `reader/drafts/`
- Voice input (Whisper) and TTS output

---

## Roadmap: TUI Enhancements

### Tier 1: High Value, Low Effort

#### Streak Tracking
Display consecutive study days in the dashboard.

```
🔥 Streak: 12 days (best: 34)
```

- Parse `schedule.json` for `last_reviewed` dates
- Add streak calculation to `core.py`
- Display in StatusPanel

#### Difficulty Calibration
Track `reset_count` for each card. Cards that repeatedly fall to box 0 indicate weak spots.

- Add `reset_count` field to schedule entries
- Surface "Hardest cards" in stats or dashboard
- Flag cards with >3 resets

#### Post-Drill Reflection
After completing a card, prompt for metacognitive reflection:
- Which proof technique did you use?
- What was the key insight?

Store technique tags in `schedule.json` or `history.jsonl`.

---

### Tier 2: High Value, Medium Effort

#### Stats Screen
Dedicated screen for visualizing progress:
- Cards by box distribution (histogram)
- Review history over time
- Domain coverage breakdown
- Weak technique identification

#### LLM Hint Integration
When stuck during drill, press `h` for a Socratic hint (not the answer).

- Send current block context to LLM
- Display one guiding question in modal
- Track hint usage in history

#### Search Across Solutions
Full-text search across all solution files from Browse screen.

- Search input widget
- Filter/highlight matching cards
- Jump to card on selection

---

### Tier 3: Higher Effort

#### Adaptive Quiz Mode
Interactive quiz that adapts difficulty based on performance.

```
knos quiz --domain analysis --chapter "Ch. 6"
```

Flow: definition → theorem → proof technique → edge cases

---

## Roadmap: Content & Workflow

### Domain Templates
Skeleton templates for manual card creation:

```
solutions/templates/
├── analysis.md      # Statement, Proof technique, Key insight
├── algorithms.md    # Invariant, Complexity, Implementation
└── ml.md            # Model, Key equations, Computational notes
```

### Connection Cards
Cross-domain synthesis cards linking concepts across domains.

---

## Implementation Priority

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
8. Domain templates

---

## Appendix: Learning Science Principles

| Principle | How the system supports it |
|-----------|---------------------------|
| **Active recall** | Line-by-line reveal forces retrieval before seeing answer |
| **Spaced repetition** | Leitner box scheduling optimizes review intervals |
| **Metacognition** | Reflection prompts; technique tagging |
| **Desirable difficulty** | Difficulty calibration surfaces weak spots |
| **Interleaving** | Domain rotation; cross-domain connection cards |
