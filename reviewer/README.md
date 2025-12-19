# Reviewer — Line-by-Line Reveal Tool

Spaced repetition for active recall without typing. See full document context, then self-assess each line before it reveals.

## Quick Start

```bash
# Launch TUI dashboard (RECOMMENDED)
./study

# CLI: Practice due solutions
./drill

# CLI: Direct reviewer access
uv run python3 -m reviewer.reviewer --focus           # All focus solutions
uv run python3 -m reviewer.reviewer --due             # Due solutions only
uv run python3 -m reviewer.reviewer --summary         # Show mastery status
```

## Workflow

1. See code line prompt: `">>> Line 1: [y/n/s/q]"`
2. Mentally recall it and press:
   - `y` = knew it ✓
   - `n` = didn't know ✗
   - `s` = skip block
   - `q` = quit session
3. Line reveals with your assessment marker
4. Score = % of lines marked `y`
5. Perfect (100%) → advance Leitner box
6. Imperfect → reset to box 0 (re-drill immediately)

## Solution Format

Solutions are Markdown files with fenced code blocks as practice targets:

```markdown
# Topic

## How It Works
[explanation, visible during practice]

## Implementation

```python
def code():
    pass
```
```

**Rules:**
- Every fenced code block is a reveal target
- Mark non-targets with `<!-- INFO -->` within 50 chars of fence
- No trailing blank lines in code blocks

## Schedule (Leitner Box)

- **Box 0** (failed): due in 1 hour
- **Box 1**: due in 4 hours
- **Box 2+**: 1d → 3d → 7d → 14d → 30d
- Perfect (100%) advances box; imperfect resets to box 0

## Setup

```bash
cd reviewer
uv sync
```
