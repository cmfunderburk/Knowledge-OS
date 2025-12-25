# Troubleshooting

Common issues and fixes for Knowledge OS.

## First-Run Issues

### "uv: command not found"

The `uv` package manager isn't installed or isn't in your PATH.

**Fix:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal or run `source ~/.bashrc` (or equivalent for your shell).

### "No module named 'knos'" or "command not found: knos"

You're running `knos` directly instead of through `uv run`.

**Fix:** Always use the `uv run` prefix:
```bash
uv run knos read      # Correct
knos read             # Won't work unless you've installed globally
```

### "Python version mismatch" or dependency errors

Knowledge OS requires Python 3.11+.

**Check your version:**
```bash
python3 --version
```

**Fix:** Install Python 3.11+ via your system package manager or [pyenv](https://github.com/pyenv/pyenv).

### "API key not configured"

The Reader requires a Gemini API key.

**Fix:**
1. Run `uv run knos init` to create config files interactively, OR
2. Copy `config/reader.yaml.example` to `config/reader.yaml` and add your key

You can also set the `GOOGLE_API_KEY` environment variable.

### LLM test fails

```bash
uv run knos read test
```

**Common causes:**
- Invalid API key (check for typos, regenerate if needed)
- Network connectivity issues
- API quota exceeded (free tier: 1500 requests/day)
- Key lacks permissions (ensure Gemini API is enabled in Google Cloud)

## Reader Issues

### Material shows "0 chapters available"

**For PDFs:**
- Verify the file exists at the registered path
- Check that `structure.chapters` is defined with valid page ranges
- Page numbers are 1-indexed PDF pages (as shown in your PDF viewer), not book page numbers

**For EPUBs:**
- Verify the file is a valid EPUB (not corrupted)
- Some EPUBs have malformed TOCs; try a different source

**Check your registration:**
```bash
uv run knos read info <material-id>
```

### "No content extracted from PDF"

**Possible causes:**
- Page range is outside the PDF's actual page count
- PDF is scanned/image-based without OCR text
- PDF is corrupted

**Debug:** Open the PDF manually and verify the page numbers match your config.

### Session not saving

**Check permissions:**
```bash
ls -la knos/reader/sessions/
```

Ensure the directory exists and is writable. If not:
```bash
mkdir -p knos/reader/sessions
```

### Dialogue feels off-topic or unhelpful

- Try switching modes with `Ctrl+M` (Socratic → Clarify for explanations)
- The tutor works best with focused questions about specific passages
- For technical content, use Technical mode for step-by-step guidance

## Drill Issues

### Card not appearing in drill queue

**Check location:** Cards must be in `solutions/focus/`, not `solutions/` root or `solutions/examples/`.

**Check format:** The file must have at least one fenced code block (triple backticks).

**Check schedule:**
```bash
uv run python3 -m knos.reviewer.reviewer --due
```

If the card isn't listed, check `plan/schedule.json` for its `next_due` time—it may not be due yet.

### Card always resets to box 0

The Leitner system requires 100% accuracy for code blocks (80% for slots blocks). Any mistake resets the card.

**Common format issues:**
- Trailing whitespace in code blocks
- Blank lines at the end of code blocks
- Invisible characters from copy-paste

**Check for trailing whitespace:**
```bash
cat -A solutions/focus/your-card.md | grep -E '\s+\$'
```

### Schedule state corrupted

If `plan/schedule.json` becomes corrupted:

```bash
rm plan/schedule.json
```

The system will regenerate it on the next drill session. You'll lose box progress for all cards.

## Voice/TTS Issues

### "CUDA not available"

Voice features require a CUDA-capable GPU.

**Check CUDA:**
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

**If False:**
- Verify you have an NVIDIA GPU
- Install CUDA drivers for your system
- Reinstall PyTorch with CUDA support

### "No audio input device"

The voice input feature can't access your microphone.

**Linux:** Ensure PulseAudio or PipeWire is running. Check with:
```bash
pactl list sources
```

**macOS:** Grant terminal microphone permissions in System Preferences → Security & Privacy → Microphone.

### TTS not speaking / cutting off

- Reduce TTS chunk size in `config/reader.yaml` (`tts.chunk_sentences`)
- Try switching backends (kokoro → chatterbox or vice versa)
- Check speaker/headphone volume and routing

## Getting Help

If your issue isn't listed here:

1. Search [existing GitHub issues](https://github.com/anthropics/claude-code/issues)
2. Open a new issue with:
   - Python version (`python3 --version`)
   - Operating system
   - Full error message
   - Output of `uv run knos read test` (if Reader-related)
   - Relevant config snippets (redact API keys)
