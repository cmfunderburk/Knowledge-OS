# Skill Authoring Guide

Principles and patterns for writing effective Claude Code skills.

## Format

### Structure

```yaml
---
name: skill-name
description: What it does and when to use it. Invoke with /skill-name.
---

# Skill Name

Core instructions...
```

**Requirements:**
- YAML frontmatter: `name` (lowercase, hyphens, max 64 chars) + `description` (max 1024 chars)
- No blank lines before opening `---`
- Spaces only (no tabs) in frontmatter

### Size

Keep SKILL.md **under 500 lines**. If larger, split into:
- SKILL.md: Essential guidance
- Reference files: Detailed tables, edge cases, examples

Use progressive disclosure: Claude loads SKILL.md first, references detail files when needed.

## The Description Field

The description determines when Claude invokes the skill. It must answer:

1. **What does it do?** - List specific capabilities
2. **When to use it?** - Include trigger terms users would say

```yaml
# Weak
description: Helps with learning

# Strong
description: Adaptive dialogue for progressive mastery of text, code, or concepts. Uses questioning to build understanding through comprehension, application, and evaluation. Invoke with /deep-learn.
```

## Style Principles

### Right Altitude

Find the Goldilocks zone between too specific (brittle) and too vague (unclear).

| Too Specific | Right Altitude | Too Vague |
|--------------|----------------|-----------|
| "If user says X, respond with Y" | "Ask clarifying questions when goals are unclear" | "Be helpful" |
| Enumerated edge cases | Representative examples | No examples |
| Explicit state machines | Behavioral guidance | "Figure it out" |

**Heuristic:** Give Claude principles and examples, not scripts.

### Token Budget

Every token competes for attention. Ask: "Does this guide behavior, or just explain design?"

**Keep:** Behaviors, constraints, examples, heuristics
**Cut:** Meta-commentary, design rationale, comparative framing

```markdown
# Cut this (meta-commentary)
This skill embeds pedagogical patterns within a continuous dialogue—maintaining
context throughout rather than delegating to separate skills.

# Keep this (behavioral)
Ask one question at a time. Wait for response before continuing.
```

### Positive Framing

Tell Claude what TO do, not what NOT to do. Negative lists introduce concepts then forbid them.

```markdown
# Weaker (negative framing)
Do NOT:
- Answer your own questions
- Explain concepts they didn't ask about
- Fill silence

# Stronger (positive framing)
Ask questions and wait for responses. Let the user drive the pace.
Only explain when explicitly asked.
```

### Examples Over Enumeration

Replace lists of rules with representative examples. Claude generalizes well.

```markdown
# Weaker (enumeration)
Question types to mix:
- Identification/factual (structured choices)
- Explanation/reasoning (text input)
- Application scenarios (present situation)
- Evaluation prompts (compare approaches)

# Stronger (example)
## Example Exchange

Claude: "Which file handles authentication first?"
[Structured choice - factual recall]

Claude: "Why do you think the middleware validates before the handler?"
[Open response - reasoning]
```

### Implicit State

Don't define explicit state machines unless Claude consistently fails without them. Claude tracks state naturally from behavioral guidance.

```markdown
# Usually unnecessary
Track internally:
| State | Values |
| level | comprehension / application / evaluation |
| mode | PROBE / VERIFY / SCAFFOLD |
| exchange_count | 0..N |

# Usually sufficient
Progress through comprehension → application → evaluation as the learner demonstrates readiness.
Offer checkpoints every 8-10 exchanges.
```

### Affirmative, Not Contrastive

Define what something IS, not what it ISN'T. Contrastive definitions introduce irrelevant concepts.

```markdown
# Introduces noise
This skill uses questioning rather than delegation to separate skills.

# Clean
This skill uses questioning to deepen understanding.
```

## Checklist

Before finalizing a skill:

- [ ] Under 500 lines (or properly split)?
- [ ] Description answers "what" and "when"?
- [ ] No meta-commentary about design?
- [ ] Positive framing (not "Do NOT" lists)?
- [ ] Examples instead of rule enumeration?
- [ ] No explicit state tracking unless proven necessary?
- [ ] No contrastive definitions?
- [ ] Every section guides behavior?

## Sources

- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude 4 Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)
