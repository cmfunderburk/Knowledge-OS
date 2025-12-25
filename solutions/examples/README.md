# Example Drill Cards

This directory contains sample drill cards demonstrating the format and variety of content that can be encoded for spaced repetition practice.

## Directory Structure

```
examples/
├── algebra/             # Mathematical concepts and formulas
│   ├── quadratic_formula.md
│   ├── function_notation.md
│   └── logarithm_properties.md
├── algorithms/          # Code implementations
│   └── binary_search.md
├── economics/           # Models and relationships
│   └── supply_demand.md
├── logic/               # Formal logic and proofs
│   └── modus_ponens.md
├── philosophy/          # Interpretive and conceptual knowledge
│   └── aristotle_four_causes.md  # Uses slots format
└── psychology/          # Conceptual knowledge
    ├── classical_conditioning.md
    ├── operant_conditioning.md   # Uses slots format
    └── research_methods.md
```

## Card Structure

Every `.md` file in `solutions/` is a drill card. The system extracts **fenced code blocks** as drill targets - content you practice recalling line-by-line.

### Template

```markdown
# Topic Name

**Source:** Textbook, Chapter X

## Overview

Context visible during practice. Explain the concept here.

## Key Concept

\`\`\`text
This block becomes a drill target.
You'll reveal it line-by-line during practice.
100% accuracy required to advance.
\`\`\`

## Related Ideas

Additional context, connections, or variations.
```

### Rules

1. **One concept per file** - Keep cards atomic and focused
2. **Every fenced block is a target** - Unless preceded by `<!-- INFO -->`
3. **2-15 lines per block** - The 100%-or-reset rule demands granularity
4. **No trailing blank lines** - Inside code blocks

### Non-Target Blocks

Use `<!-- INFO -->` to mark blocks that shouldn't be drilled:

```markdown
<!-- INFO -->
\`\`\`bash
# Example output, not a drill target
$ ./study --today
\`\`\`
```

### Slots Format

For conceptual cards with multiple related items (3+), use `slots` blocks instead of `text`:

```markdown
## Key Terms

\`\`\`slots
Term 1 :: Definition of term 1
Term 2 :: Definition of term 2
Key difference :: What distinguishes them
\`\`\`
```

**Format:**
- Each drillable line: `Prompt :: Answer`
- Lines without `::` are headers (displayed but not drilled)
- Requires 80% accuracy to advance (vs 100% for code blocks)

**When to use:**
- **Code/text blocks**: Executable code, algorithms, short single-concept definitions
- **Slots blocks**: Multi-item conceptual cards (definitions with properties, processes with steps, distinctions)

## Content Types

Cards can encode many types of knowledge:

| Type | Example | Block Language |
|------|---------|----------------|
| Code | Algorithms, data structures | `python`, `javascript`, etc. |
| Proofs | Logic rules, theorems | `text` or `lean` |
| Definitions | Single terms or concepts | `text` |
| Multi-term definitions | Related terms with properties | `slots` |
| Formulas | Equations, relationships | `text` with symbols |
| Procedures | Step-by-step processes | `slots` (Step N :: action) |
| Distinctions | Comparing similar concepts | `slots` (A :: trait, B :: trait) |
| Interpretive concepts | Philosophical frameworks | `slots` |
| Models | Diagrams in text form | `text` with ASCII art |

## Humanities vs. STEM Cards

Knowledge OS works for both procedural knowledge (algorithms, formulas) and interpretive knowledge (philosophical concepts, literary analysis, historical frameworks).

**Procedural cards** typically use code or text blocks with exact content to reproduce. The goal is precise recall—you need to reproduce the algorithm or formula correctly.

**Interpretive cards** typically use slots blocks with key concepts and their meanings. The goal is not exact reproduction but recalling the essential distinctions, relationships, and frameworks. The 80% threshold for slots blocks reflects this: you're demonstrating understanding of the conceptual landscape, not rote memorization.

**Examples:**
- `algorithms/binary_search.md` — Procedural (code block, 100% accuracy)
- `philosophy/aristotle_four_causes.md` — Interpretive (slots block, 80% accuracy)

## Getting Started

1. Copy these examples to `solutions/focus/` to practice with them
2. Create your own cards based on what you're learning
3. Run `uv run knos drill` to practice
4. Run `uv run knos` to see the dashboard
