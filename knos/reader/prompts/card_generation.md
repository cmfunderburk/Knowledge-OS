# Card Generation from Reading Dialogues

You are generating **drill cards** from a reading session. You have access to:
1. The original chapter content the user was studying
2. The full dialogue transcript between user and reading companion

Your task: identify concepts worth drilling and generate card drafts.

---

## Philosophy

**Not everything deserves a card.** The dialogue reveals what the user actually engaged with. Generate cards for concepts where you see:

- **Clarify mode exchanges** — User needed direct explanation; reinforce this
- **Extended back-and-forth** — Deep engagement signals importance
- **Repeated questions** — Concept was difficult or confusing
- **Challenge mode success** — User defended understanding; worth cementing
- **"Aha" moments** — Breakthroughs in understanding

Ignore concepts the user skimmed past or already demonstrated mastery of.

---

## Card Format Specification

Cards are Markdown files for a spaced-repetition system. The user reveals fenced code blocks line-by-line and self-assesses recall.

### Parsing Rules

1. **Drill targets**: Any fenced code block is drilled (code blocks or slots blocks)
2. **Non-drill blocks**: Prefix with `<!-- INFO -->` within 50 chars of the fence
3. **Block size**: 2-15 lines ideal, 20 max. No trailing blank lines inside fence
4. **Atomicity**: One concept per card. If tempted to write "Part 1/Part 2", make two cards

### Block Types

There are two types of drill blocks:

**Code blocks** (`python`, `text`, `lean`) — Line-by-line recall
- User sees nothing, reveals one line at a time
- Requires 100% accuracy to advance
- Best for: executable code, algorithms, formulas, short single-concept definitions

**Slots blocks** (`slots`) — Prompt-answer recall
- User sees prompts, must recall corresponding answers
- Requires 80% accuracy to advance
- Best for: multi-item conceptual cards (3+ related items)

**Decision heuristic**: If the card has 3+ related items to recall (steps, terms, comparisons), use `slots`. For executable code or single definitions, use code blocks.

### Slots Format

```slots
Prompt text :: Answer text
Another prompt :: Another answer
```

- Each drillable line: `Prompt :: Answer`
- Lines without `::` are headers (displayed but not drilled)
- Empty lines organize content

### Language Tags

- `python` — algorithms, data structures, code patterns
- `text` — short definitions, single-concept explanations
- `lean` — Lean 4 tactics (if applicable)
- `slots` — multi-item conceptual recall (definitions with properties, processes with steps, distinctions)

---

## Card Templates

Select the appropriate template based on content type. The `text` block is always the drill target—what the user will recall from memory.

---

### Template: Algorithm

**Use for:** Code implementations, data structure operations, computational procedures.

`````markdown
# Algorithm Name

**Time:** O(...) | **Space:** O(...)

## How It Works

[Mechanism, key insight, invariants - 2-4 sentences]

## Implementation

[Brief intro sentence]

```python
def algorithm():
    # implementation
```

## When to Use

- [Constraint or trade-off]
- [Edge case consideration]
`````

---

### Template: Concept

**Use for:** Technical terms, abstract ideas, definitions with multiple properties to recall.

`````markdown
# Concept Name

**Source:** [Book Title, Chapter N]

## Definition

```slots
Term :: [precise definition]
Key property :: [important characteristic]
Related to :: [connection to other concepts]
```

## Why It Matters

[One sentence connecting to broader context]
`````

**Note:** For simple single-line definitions, use `text` blocks instead.

---

### Template: Process

**Use for:** Ordered steps, methodologies, procedures to follow.

`````markdown
# Process Name

**Source:** [Book Title, Chapter N]

## When to Use

[One sentence describing the situation that calls for this process]

## Steps

```slots
Step 1 :: [action or description]
Step 2 :: [action or description]
Step 3 :: [action or description]
```

## Key Insight

[One sentence on why this ordering matters or common mistakes]
`````

---

### Template: Distinction

**Use for:** Contrastive pairs, differentiating similar concepts, taxonomic boundaries.

`````markdown
# [Concept A] vs [Concept B]

**Source:** [Book Title, Chapter N]

## The Distinction

```slots
[Concept A] :: [defining characteristic]
[Concept B] :: [defining characteristic]
Key difference :: [what separates them]
```

## When It Matters

[One sentence on why this distinction is practically important]
`````

---

### Template: Framework

**Use for:** Mental models, structured ways of thinking, analytical lenses.

`````markdown
# Framework Name

**Source:** [Book Title, Chapter N]

## Overview

[One sentence describing what this framework is for]

## Structure

```slots
[Component 1] :: [brief description]
[Component 2] :: [brief description]
[Component 3] :: [brief description]
```

## Application

[One sentence on how to use this framework in practice]
`````

---

### Template: Principle

**Use for:** Core maxims, guiding rules, heuristics worth internalizing.

`````markdown
# Principle: [Name or Short Form]

**Source:** [Book Title, Chapter N]

## Statement

```text
[The principle in memorable form]
```

## Rationale

[2-3 sentences on why this principle holds and when it applies]
`````

**Note:** Principles are typically single statements—use `text` blocks. Use `slots` only if there are multiple related principles to compare.

---

### Template: Proof Strategy

**Use for:** Mathematical proof techniques, logical argument patterns.

`````markdown
# Proof Strategy: [Name]

**Use when:** [Goal form, e.g., "To prove P → Q"]

## Template

```text
Proof. [Setup]
  [Step 1]
  [Step 2]
  Therefore [conclusion].
∎
```

## Key Insight

[One paragraph on the intuition behind this strategy]
`````

---

## Output Format

Return cards in this format for parsing:

```
===CARD===
[full markdown content of card 1]
===CARD===
[full markdown content of card 2]
===CARD===
...
```

Use `===CARD===` as the delimiter between cards. Generate 1-5 cards per chapter session, focusing on quality over quantity.

---

## Analysis Process

1. Read the chapter content to understand the source material
2. Read the dialogue transcript to see what the user focused on
3. Identify 1-5 concepts that show engagement signals (see Philosophy above)
4. For each concept, select the most appropriate template
5. Draft the card with minimal context—user already learned this; cards reinforce recall
6. Verify each card: atomic, correct template, drill block properly sized (2-15 lines)

**Remember:** The user will review these drafts before adding them to their deck. When uncertain about a concept's card-worthiness, lean toward including it—they can discard. But don't pad with low-value cards.
