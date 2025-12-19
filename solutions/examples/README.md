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
└── psychology/          # Conceptual knowledge
    ├── classical_conditioning.md
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

## Content Types

Cards can encode many types of knowledge:

| Type | Example | Block Language |
|------|---------|----------------|
| Code | Algorithms, data structures | `python`, `javascript`, etc. |
| Proofs | Logic rules, theorems | `text` or `lean` |
| Definitions | Terminology, concepts | `text` |
| Formulas | Equations, relationships | `text` with symbols |
| Procedures | Step-by-step processes | `text` numbered list |
| Models | Diagrams in text form | `text` with ASCII art |

## Getting Started

1. Copy these examples to `solutions/focus/` to practice with them
2. Create your own cards based on what you're learning
3. Run `./drill` to practice
4. Check `./study` dashboard to see your progress
