# Screenshots Needed

This directory should contain static screenshots for documentation. While video demos exist, static images are needed for contexts where video doesn't render (GitHub mobile, offline docs, accessibility).

## High Priority

These screenshots would most improve the entry-point documentation:

| Filename | Description | Where Used |
|----------|-------------|------------|
| `dashboard.png` | Main TUI dashboard showing due cards and study plan | README |
| `reader-material-select.png` | Material selection screen with bundled classics visible | GETTING_STARTED |
| `reader-chapter-select.png` | Chapter selection showing Study Tools menu option | GETTING_STARTED |
| `reader-dialogue.png` | Active dialogue session with mode indicator visible | README, GETTING_STARTED |
| `drill-session.png` | Drill TUI mid-session, showing line-by-line reveal | README |

## Medium Priority

| Filename | Description | Where Used |
|----------|-------------|------------|
| `reader-quiz-mode.png` | Quiz session in progress | USAGE |
| `reader-mode-switch.png` | Mode selection overlay (Ctrl+M) | USAGE |
| `drill-card-complete.png` | Card completion showing box advancement | USAGE |
| `reader-card-generation.png` | Card generation dialog (Ctrl+G) | GETTING_STARTED |

## Capture Instructions

1. **Terminal size:** Use a reasonable dimension (~120x40 characters)
2. **Content:** Load sample content so screens aren't empty
3. **Format:** PNG, no transparency needed
4. **Themes:** Consider capturing both light and dark terminal themes
5. **Clean state:** Hide any personal data or non-example content

### Recommended Setup

```bash
# Ensure bundled content is registered
uv run knos init

# For Reader screenshots
uv run knos read
# Select "Nicomachean Ethics" → Book I for dialogue screenshots

# For Drill screenshots
# First ensure some cards exist in solutions/focus/
uv run knos drill
```

### Capture Tools

- **Linux:** `gnome-screenshot`, `flameshot`, or `scrot`
- **macOS:** Cmd+Shift+4 or `screencapture`
- **Cross-platform:** Most terminals support "Save as image" or export

## Existing Media

The following video demos already exist in this directory:

| File | Content |
|------|---------|
| `Aristotle-Reader.mp4` | Reader dialogue with Nicomachean Ethics |
| `DonQuixote-Reader.mp4` | Opening question for Don Quixote |
| `Photoelectric-Reader.mp4` | Technical article (Einstein 1905) |
| `last-question-chat.md` | Transcript of a sample dialogue |

These are embedded in README.md using `<details>` blocks.
