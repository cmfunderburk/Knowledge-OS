# Knowledge OS Manifesto

A foundational vision for rigorous self-study.

---

## Vision

This repository is a **Knowledge Operating System**: a unified engine for acquiring, encoding, and retaining PhD-level understanding. It treats learning as a systems problem—reducible to pipelines, feedback loops, and measurable state.

The system does not merely store knowledge. It **processes** knowledge: transforming passive reading into active recall targets, surfacing what needs attention, and compounding mastery over time.

---

## Core Principles

### 1. Single Source of Truth

All study state lives in the filesystem. Markdown files are the database. `plan/schedule.json` is the scheduler state. `history.jsonl` is the audit log. No external services, no hidden state.

### 2. Separation of Content and Engine

The engine (Python code) is versioned in git. The content (solutions, textbooks, schedules) is gitignored and lives locally. They evolve independently. Sharing the engine does not expose the learning journey.

### 3. Active Recall as the Primitive

The atomic unit is the **drill target**: a fenced code block revealed line-by-line. The format is code blocks; the content is not limited to code. Proof templates, tactic sequences, logical laws, formal definitions—anything that can be usefully encoded as a line-by-line reveal is valid. The surrounding markdown provides flexible context. If knowledge cannot be drilled, it is not yet understood.

### 4. Strict Spaced Repetition

The Leitner box enforces overlearning. 100% accuracy advances; any failure resets. This is not punitive—it ensures the "tip of the tongue" state where consolidation happens. The intervals are fixed: 1h → 4h → 1d → 3d → 7d → 14d → 30d.

### 5. Closed Feedback Loops

Every workflow forms a loop:
- **Read → Encode → Drill → Master** (content acquisition)
- **Drill → Fail → Source → Re-read → Drill** (remediation)
- **Study → Log → Analyze → Adjust** (meta-optimization)

Open loops leak energy. The system's job is to close them.

### 6. Proactive, Not Reactive

The system should tell you what to do next. It knows what's due, what's overdue, what's struggling. The default state is: launch the TUI, see the critical path, execute.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     TUI (./study)                       │
│              Dashboard · Drill · Browse                 │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Core Library                          │
│         reviewer/core.py — shared data layer            │
│    (scheduling, parsing, history, state management)     │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    Filesystem                           │
│   solutions/              history.jsonl                 │
│   plan/                   (schedule, config, todo)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Reader (./read)                        │
│       Material Selection · Chapter · Dialogue           │
├─────────────────────────────────────────────────────────┤
│  reader/llm.py      — LLM providers (Gemini, Anthropic) │
│  reader/content.py  — PDF extraction, chapter loading   │
│  reader/prompts/    — Dialogue mode templates           │
├─────────────────────────────────────────────────────────┤
│  Textbooks/         — Source PDFs                       │
│  reader/extracted/  — Pre-extracted chapter markdown    │
└─────────────────────────────────────────────────────────┘
```

The TUI is the command center. The core library is the engine. The filesystem is the database. The Reader is the acquisition interface—transforming passive reading into active dialogue. All interfaces share the same core library—no duplication, no drift.

---

## Key Capabilities

### Card Authoring Pipeline

**Problem:** Creating drill-ready cards from source material requires too many manual steps.

**Vision:** A streamlined pipeline from source → card:
- Ingest source material (PDF, textbook, notes)
- Select content worth encoding
- Generate card with correct structure (via LLM or template)
- Review and refine
- Publish to focus queue

The friction to create a new card should approach zero. Every insight captured in the moment, not deferred.

### Lean Integration

**Problem:** Lean 4 proofs are perfect drill targets but live outside the system.

**Vision:** Encode Lean content as standard markdown cards—no special parsing required:
- Extract lessons from educational resources (Natural Number Game, Mathematics in Lean, Theorem Proving in Lean 4)
- Decompose into atomic cards: proof templates, tactic syntax, concrete theorems
- Use `lean` fenced code blocks as drill targets
- The existing reviewer system handles them without modification

Proof practice and code practice unified in one system, using the same card format.

### Reader: LLM-Powered Study Companion

**Problem:** The autodidact lacks the corrective pressure of instructors and peers. Passive reading produces illusion of understanding.

**Solution:** The Reader module (`./read`) provides structured dialogue with source material:

- **Dialogue modes**: Socratic questioning, clarification, challenge, quiz, teach-back
- **Chapter extraction**: PDFs → markdown for efficient context caching
- **Provider flexibility**: Gemini (with context caching) or Anthropic
- **Prompt templates**: Jinja2-based, easily customizable per learning style

The Reader closes the loop between reading and encoding. A chapter session surfaces gaps; those gaps become drill cards.

**Planned extensions:**
- **Card generation**: Transform dialogue insights into drill-ready content
- **Session synthesis**: Connect today's reading to prior sessions and existing cards

The LLM is a tool, not a crutch. It amplifies effort; it does not replace it.

### Analytics

**Problem:** `history.jsonl` accumulates data but provides no insight.

**Vision:** Actionable learning intelligence:
- Velocity tracking (cards/day, accuracy trend)
- Struggle identification (high-reset cards, slow-to-master topics)
- Mastery projection (when will card X reach box 6?)
- Domain breakdown (where is effort going?)

Data exists to inform decisions. Surface it.

---

## Design Constraints

1. **Python + Textual**: The TUI is built on Textual. CLI tools use Typer/Rich. No web stack.

2. **Minimal dependencies**: `uv` for environment management. Dependencies should fit on one screen.

3. **Filesystem as database**: No SQLite, no external services. Markdown + JSON + JSONL.

4. **Atomic cards**: One concept per file. Multiple drill blocks are fine when logically inseparable (e.g., `merge` and `merge_sort` as companion functions). Small drill targets (2-15 lines per block). The 100%-or-reset rule demands granularity.

5. **Offline-first**: The system works without network. LLM integration is opt-in enhancement.

---

## What This Document Is Not

This manifesto defines vision and principles. It does not specify:
- Implementation details (see `docs/specs/`)
- Feature roadmaps (see `docs/specs/roadmap.md`)

Those documents operationalize this vision. This document anchors them.

---

*Last updated: 2025-12-17*
