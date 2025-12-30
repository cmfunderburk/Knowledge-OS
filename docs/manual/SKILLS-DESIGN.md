# Claude Code Skills Ecosystem Design

This document captures the design decisions for a loosely-coupled skill ecosystem in Claude Code, focused on learning, comprehension, and synthesis workflows.

## Context & Goals

**User Profile:**
- Mixed technical work (development + research + learning + writing)
- Project-driven usage (intensive during specific projects)
- Mixed-format knowledge base (PDFs, docs, notes, code)
- Primary pain points: learning/retention, code comprehension, writing/synthesis

**Design Principles:**
- Skills are self-contained (no shared base prompt)
- Loose coupling: skills can reference each other via output-as-input, shared context, or explicit handoff
- Artifacts save to `./skilldocs/` by default (configurable)
- Light persona (consistent but subtle)
- Naming: mixed convention (use what's intuitive per skill)

## Claude Code's Unique Advantages

These skills leverage capabilities that static-text tools (like KnOS) cannot:

| Capability | How Skills Use It |
|------------|-------------------|
| File system access | Read local files, write artifacts |
| Web access | Fetch docs, verify claims |
| Code execution | Run commands, verify implementations |
| Multi-agent exploration | Parallel deep dives via Task tool |
| Tool-mediated interaction | AskUserQuestion for structured input |

## Skill Ecosystem

### Priority & Status

| Priority | Skill | Category | Status | Description |
|----------|-------|----------|--------|-------------|
| 1 | `/quiz` | Learning | Built | Test recall on natural language/math material |
| 2 | `/architecture` | Comprehension | Built | Map codebase structure, produce documentation |
| 3 | `/socratic` | Learning | Built | Probing questions to deepen thinking |
| 4 | `/explore-quiz` | Learning | Built | Claude explores codebase, then quizzes |
| 5 | `/teach-back` | Learning | Built | User explains, Claude verifies against sources |
| 6 | `/deep-learn` | Learning | Built | Adaptive mastery dialogue; orchestrates other learning skills |
| 7 | `/synthesize` | Output | Future | Combine multiple sources into coherent output |
| 8 | `/pattern-extract` | Extraction | Future | Identify reusable patterns, save to KB |
| 9 | `/capture` | Utility | Future | Save insights to knowledge base |

### Coupling Model

```
         ┌──────────────┐
         │   Material   │  (files, URLs, conversation)
         └──────┬───────┘
                │
                ▼
         ┌─────────────┐
         │ /deep-learn │  (orchestrator)
         └──────┬──────┘
                │ invokes patterns from
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌──────────┐ ┌─────────┐ ┌────────────┐
│/socratic │ │/explore-│ │/teach-back │
│          │ │  quiz   │ │            │
└──────────┘ └─────────┘ └────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐  ┌─────────┐  ┌───────────┐
│ /quiz │  │artifacts│  │/synthesize│
│       │  │         │  │           │
└───┬───┘  └────┬────┘  └─────┬─────┘
    │           │             │
    └─────┬─────┴─────────────┘
          │
          ▼  (explicit handoff or artifact)
    ┌───────────┐
    │ /capture  │ ──▶ Knowledge Base
    └───────────┘
```

---

## Skill Specifications

### `/quiz` (Built)

**Purpose:** Test comprehension and recall on natural language or mathematical material.

**Invocation:**
```
/quiz --article [path or URL]     # Academic paper, essay, news article
/quiz --technical [path or URL]   # Technical book, documentation
/quiz --story [path or URL]       # Short story, fiction
/quiz --novel [path or URL]       # Novel (may focus on chapters)
/quiz --math [path or URL]        # Mathematical text, proofs
```

**Behavior:**
- Load content from path, URL, or conversation context
- Apply mode-specific focus (thesis for articles, plot for stories, etc.)
- Mix question formats:
  - `AskUserQuestion` for factual recall (definitions, sequences, identification)
  - Conversational for analytical/interpretive questions
- Provide feedback after each answer
- Track score informally
- After 5-7 questions, offer to continue or wrap up

**Location:** `.claude/skills/quiz/SKILL.md`

---

### `/architecture` (Next)

**Purpose:** Explore a codebase and produce thorough architecture documentation.

**Invocation:**
```
/architecture                     # Current directory
/architecture src/                # Specific path
/architecture --focus "auth"      # Focus on specific area
/architecture --depth shallow     # Quick overview only
/architecture --questions         # Include "questions for the team" section
```

**Default:** Deep documentation (onboarding-quality, comprehensive but organized).

**Phases:**

1. **Exploration** (via Task tool with Explore agent)
   - Map directory structure
   - Identify key files (entry points, configs, types/interfaces)
   - Trace imports and dependencies
   - Note file organization patterns

2. **Analysis**
   - Identify architectural patterns (MVC, repository, event-driven, etc.)
   - Map data flow between components
   - Identify key abstractions and their relationships
   - Note design decisions (explicit or inferred)

3. **Output**
   - Produce structured markdown document
   - Save to `./skilldocs/architecture-{project}-{date}.md`

**Output Format:**
```markdown
# Architecture: {project}

## Overview
{2-3 paragraph executive summary}

## Directory Structure
{Tree diagram with annotations}

## Module Map
| Module | Responsibility | Key Files | Dependencies |
|--------|----------------|-----------|--------------|
| ...    | ...            | ...       | ...          |

## Key Abstractions
### {Abstraction Name}
- Purpose: ...
- Location: ...
- Used by: ...

## Data Flow
{Mermaid diagram or structured description}

## Patterns
### {Pattern Name}
- Where: {files/modules}
- Implementation: {brief description}
- Why: {rationale if apparent}

## Entry Points
| Entry Point | Purpose | Triggers |
|-------------|---------|----------|
| ...         | ...     | ...      |

## Configuration
{Key config files and what they control}

## Notes
{Observations, potential issues, architectural debt}

## Questions (optional, with --questions)
{Things Claude couldn't determine, worth asking the team}
```

---

### `/socratic` (Planned)

**Purpose:** Deepen thinking through probing questions rather than providing answers.

**Invocation:**
```
/socratic                         # General mode
/socratic "topic or question"     # Start with specific focus
```

**Scope:** General purpose - works with code, writing, ideas, decisions.

**When to use:**
- Before writing (clarify your thinking)
- After reading (surface assumptions)
- During design (stress-test decisions)
- When stuck (find the real question)

**Behavior:**
- Ask one probing question at a time
- Follow threads that reveal confusion or insight
- Surface unstated assumptions
- Identify contradictions or gaps in reasoning
- Draw out through questions - don't lecture
- Help user articulate their own conclusion
- Light persona: curious, patient, genuinely interested

**Types of questions:**
- "What would have to be true for that to work?"
- "What's the strongest argument against this?"
- "What are you assuming about X?"
- "Why does that matter?"
- "What would change your mind?"
- "What happens if that fails?"

**Exit:** When user has articulated a clear position or decision, summarize what emerged.

---

### `/explore-quiz` (Planned)

**Purpose:** Claude explores a codebase, then quizzes the user on what it found.

**Invocation:**
```
/explore-quiz                     # Whole codebase
/explore-quiz src/auth/           # Specific area
/explore-quiz "error handling"    # Specific concern
```

**Phases:**

1. **Exploration** (via Task tool)
   - Understand structure, patterns, key modules
   - Identify interesting/important areas

2. **Summary**
   - Present what was found
   - Preview what the quiz will cover
   - Let user adjust focus

3. **Quiz**
   - Questions that can be verified against actual code
   - `AskUserQuestion` for identification (which module, what pattern)
   - Conversational for explanation questions
   - Can re-explore during quiz to verify answers

---

### `/teach-back` (Future)

**Purpose:** User explains a concept, Claude verifies against authoritative sources.

**Unique value:** Claude can check against files, documentation, web sources to verify accuracy.

**Flow:**
1. User explains concept/system/code
2. Claude identifies claims
3. Claude verifies each claim against sources
4. Feedback: what's correct, what's incomplete, what's wrong

---

### `/synthesize` (Future)

**Purpose:** Combine multiple sources into coherent, unified output.

**Inputs:** Files, URLs, conversation context (multiple sources).

**Outputs:** Structured document that synthesizes across sources.

**Modes:**
- Comparison (how sources agree/disagree)
- Integration (unified narrative)
- Summary (key points from all)

---

### `/pattern-extract` (Future)

**Purpose:** Identify reusable patterns in code and save to knowledge base.

**Output:** Pattern documentation in a consistent format, saved to KB.

---

### `/capture` (Future)

**Purpose:** Save insights from current session to knowledge base.

**Behavior:** Take conversation context, extract key insights, write to appropriate location in user's format.

---

## Implementation Notes

### File Locations
```
.claude/skills/
├── quiz/SKILL.md           # Built
├── architecture/SKILL.md   # Next
├── socratic/SKILL.md       # Planned
└── explore-quiz/SKILL.md   # Planned

./skilldocs/                 # Default output location for artifacts
```

### Settings (Future)
Could support `.claude/settings.json` for:
- Custom artifact output location
- Default flags per skill
- Persona adjustments

### Iteration Approach
- Build and test one skill at a time
- Refine based on actual usage
- Add skills as needs emerge
- Keep skills independent (no shared base to maintain)
