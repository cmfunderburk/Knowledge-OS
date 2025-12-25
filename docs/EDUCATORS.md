# For Educators

Guidance for using Knowledge OS in classroom or study group settings.

## How It Fits

Knowledge OS complements human instruction—it doesn't replace it. The Reader is most effective for:

- **Independent reading practice** — Students work through assigned texts with structured dialogue
- **Pre-class preparation** — Engage with material before discussion
- **Review and consolidation** — Return to chapters after lecture
- **Self-paced catch-up** — Students who fall behind can work through material at their own pace

The LLM tutor asks questions rather than lectures. It's designed to make students articulate and defend their understanding, not to deliver content.

## Deployment Options

### Individual Student Installation

Each student installs Knowledge OS on their own machine and manages their own API key.

**Pros:** Simple, no shared infrastructure, students own their data
**Cons:** Each student needs a Gemini API key (free tier available)

**Setup per student:**
```bash
git clone <repo-url>
cd knos
uv sync
uv run knos init   # Each student enters their own API key
```

### Shared Content Registry

Distribute a pre-configured `config/content.yaml` with course materials already registered.

1. Create a `content.yaml` with your course readings
2. Share via course repository or LMS
3. Students copy to their `config/` directory

This ensures consistent material IDs and chapter definitions across the class.

### Session Export for Review

Students can export their dialogue sessions for instructor review:

```bash
uv run knos read export <material-id> <chapter> -o session.md
```

Use this for:
- Formative assessment of reading engagement
- Identifying common misconceptions
- Grading participation in reading assignments

## Creating Course Materials

### Pre-configured Content Registry

Example `content.yaml` for a philosophy course:

```yaml
materials:
  republic:
    title: "The Republic"
    author: "Plato"
    source: "knos/reader/books/republic/source.epub"

  nicomachean-ethics:
    title: "Nicomachean Ethics"
    author: "Aristotle"
    source: "knos/reader/classics/nicomachean-ethics.epub"
```

Distribute this file with your course materials. Students place source files in the specified paths.

### Course Drill Cards

Create a `solutions/` directory with course-specific drill cards:

```
solutions/
└── course-phil101/
    ├── plato-forms.md
    ├── aristotle-four-causes.md
    └── ...
```

Distribute via course repository. Students can add these to their own installation.

### Assignment Patterns

**Reading assignment:**
1. Read Chapter X before class
2. Complete a 15-minute Reader session (any mode)
3. Export session and submit

**Comprehension check:**
1. Use Quiz mode (Study Tools menu) after reading
2. Screenshot or export quiz results

**Deep engagement:**
1. Start in Socratic mode
2. Switch to Teach mode to explain a key concept
3. Generate drill cards for concepts you found difficult

## Pedagogical Considerations

### When LLM Tutoring Helps

- **Reading comprehension practice** — Structured questioning about specific passages
- **Retrieval practice** — Quiz mode for testing recall
- **Elaboration** — Teach mode reveals gaps in understanding
- **Self-paced review** — Students work at their own speed

See [PEDAGOGY.md](PEDAGOGY.md) for the learning science behind these approaches.

### When Human Instruction is Essential

- **Introducing new concepts** — The tutor probes understanding; it doesn't introduce ideas
- **Emotional and motivational support** — An LLM can't provide encouragement the way a teacher can
- **Assessment for grades** — The system is for practice, not high-stakes evaluation
- **Correcting persistent misconceptions** — Sometimes direct instruction is more efficient

### Monitoring Student Progress

Currently available:
- Session exports (`knos read export`)
- Drill progress (`plan/schedule.json` or `uv run knos progress`)

Not yet available:
- Centralized progress dashboards
- Aggregate analytics across students

## Privacy Considerations

### Data Flow

| Data | Where it goes |
|------|---------------|
| Dialogue transcripts | Stored locally in `knos/reader/sessions/` |
| Reading content | Sent to Google Gemini API during sessions |
| Student messages | Sent to Google Gemini API during sessions |
| Drill card state | Stored locally in `plan/schedule.json` |

### Institutional Policies

Before deploying in a course:

1. **Review your institution's AI policy** — Some prohibit LLM use in coursework
2. **Inform students about data sharing** — Messages and text content are sent to Google
3. **Consider content sensitivity** — Avoid copyrighted or sensitive materials
4. **Document the tool's role** — Is it required? Optional? Extra credit?

### Minimizing Data Exposure

- Use public domain texts (bundled classics, Project Gutenberg)
- Advise students to avoid sharing personal information in dialogue
- Voice features can be disabled in `config/reader.yaml`
- Drill system works entirely offline

## Getting Started

1. Review [Getting Started](GETTING_STARTED.md) for installation
2. Try the bundled classics to understand the experience
3. Create a test `content.yaml` with one course reading
4. Develop assignment patterns that fit your course
5. Pilot with a small group before full deployment
