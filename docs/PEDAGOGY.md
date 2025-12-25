# Prompting LLMs for Human Learning

This document explores how to design prompts that guide LLMs toward being effective learning companions. It draws on learning science research, documents what's been implemented in the Reader module, and brainstorms approaches not yet built.

---

## Pedagogical Foundations

### Why This Is Hard

LLMs are trained to be helpful. Often, this means providing answers. But learning research consistently shows that **struggle is productive**—the effort of retrieval, the discomfort of confusion, the work of articulation are where learning happens. A "helpful" LLM that short-circuits this process may feel satisfying while undermining retention.

The challenge: prompt LLMs to be helpful in ways that serve long-term learning rather than short-term satisfaction.

### Key Concepts from Learning Science

**Desirable Difficulties** (Bjork & Bjork)
Conditions that make learning harder in the moment but improve long-term retention. Examples: spacing, interleaving, retrieval practice, generation (producing answers rather than recognizing them). Implication for prompts: don't make things too easy.

**Zone of Proximal Development** (Vygotsky)
The space between what a learner can do alone and what they can do with guidance. Effective tutoring operates in this zone—not so easy it's boring, not so hard it's frustrating. Implication: LLM should calibrate to the learner's current understanding.

**Retrieval Practice** (Roediger & Karpicke)
Testing isn't just assessment—it's a learning event. The act of retrieving information strengthens memory more than re-reading. Implication: asking questions is more valuable than giving explanations.

**Elaborative Interrogation** (Pressley et al.)
Asking "why" and "how" questions forces learners to connect new information to existing knowledge, improving comprehension and retention. Implication: probe for explanations, not just facts.

**The Testing Effect / Generation Effect**
Information that learners generate themselves is remembered better than information they passively receive. Implication: prefer questions that make learners produce answers over explanations that hand them answers.

**Metacognition** (Flavell)
Awareness of one's own thinking and learning processes. Skilled learners monitor their understanding and adjust strategies. Implication: prompt reflection ("What's still unclear?" "How confident are you?").

**Bloom's Taxonomy** (Revised: Anderson & Krathwohl)
Hierarchy of cognitive processes: Remember → Understand → Apply → Analyze → Evaluate → Create. Lower levels are prerequisites for higher. Implication: match questioning to appropriate level; scaffold upward.

**Cognitive Load Theory** (Sweller)
Working memory is limited. Extraneous load (poorly designed instruction) competes with germane load (productive learning effort). Implication: keep prompts focused; don't overwhelm with tangents.

---

## The St. John's College Model

The Reader module draws explicitly from the [St. John's College](https://www.sjc.edu/) seminar tradition. This model embodies several pedagogically sound principles:

### Tutors, Not Professors

Faculty are "tutors" who position themselves as fellow inquirers rather than authorities. This matters because:
- It shifts responsibility for understanding to the learner
- It models intellectual humility and genuine inquiry
- It avoids the "answer dispenser" dynamic that undermines learning

### The Text as Authority

When disagreements arise, the resolution is "let's look at what the text says." This:
- Keeps discussion grounded in shared evidence
- Prevents the tutor from becoming the source of truth
- Develops close reading skills

### The Opening Question

Seminars begin with a genuine question—not rhetorical, not leading. This:
- Models that understanding requires inquiry
- Invites the learner into active engagement
- Establishes that the tutor doesn't have all the answers

### Collaborative, Not Adversarial

The goal is shared understanding, not scoring points. When material is technical, those with expertise help others reach a common level so exploration can continue.

---

## Core Prompt Design Principles

These principles emerge from both learning science and practical experimentation:

### 1. Questions Over Answers

The default should be asking, not telling. When a learner asks a question, the most pedagogically useful response is often another question that helps them find the answer themselves.

**Exception**: When the learner is genuinely stuck and lacks the prerequisite knowledge to make progress, direct explanation becomes necessary. But return to questioning as soon as scaffolding permits.

### 2. Ground in the Source Material

LLMs tend to drift into generic explanations or hallucinated details. Constantly anchoring responses to specific passages:
- Prevents hallucination
- Develops close reading habits
- Keeps discussion concrete

### 3. Demand Precision

Vague language often hides vague thinking. Pressing for clarity ("What exactly do you mean by X?") forces the learner to sharpen their understanding.

### 4. Resist Validation Theater

LLMs are trained to be agreeable, producing excessive praise ("Great question!", "Exactly right!", "You've really grasped this!"). This:
- Feels hollow after the first instance
- Halts productive inquiry
- Can validate incorrect understanding
- Undermines the learner's ability to self-assess

Better: engage with the substance directly. Build on it, complicate it, probe deeper.

### 5. Calibrate to the Learner

The same material requires different approaches for novices vs. experts. Signals of understanding (or confusion) should modulate difficulty, question type, and scaffolding level.

### 6. Make Thinking Visible

Ask learners to articulate their reasoning, not just their conclusions. "How did you arrive at that?" reveals (and strengthens) understanding in ways that "What's the answer?" cannot.

---

## Implemented Modes

> **Status:** All modes in this section are fully implemented and available via `Ctrl+M` during Reader sessions (except Review, which is accessed via the Study Tools menu).

The Reader uses a two-layer prompt architecture: a **base prompt** establishing identity and context, plus **mode prompts** that modify behavior. This allows mid-session switching without losing conversation state.

### Base Prompt Philosophy

The base prompt (`base.md`) establishes:
- Identity as a "fellow traveler in understanding"
- The text as shared authority
- Core principles (ask don't tell, ground in text, demand precision)
- Anti-patterns to avoid (excessive praise, lecturing, text drift)

Mode prompts add behavioral instructions without repeating the base.

### Socratic (Default)

**Pedagogical rationale**: Socratic questioning is a form of elaborative interrogation—it forces learners to examine assumptions, trace implications, and articulate understanding. It operationalizes "retrieval practice" through dialogue.

**Techniques**:
- Clarifying questions: "What do you mean by...?"
- Probing assumptions: "Why do you think that's true?"
- Probing evidence: "What in the text supports that?"
- Exploring implications: "If that's true, then what follows?"
- Questioning the question: "Is that the right question to ask?"

**When it works**: Learner has enough foundation to engage productively; exploring interpretive or analytical questions.

**When it fails**: Learner lacks prerequisite knowledge; question requires factual lookup, not reasoning.

### Clarify

**Pedagogical rationale**: Sometimes learners are genuinely stuck—they lack the prerequisite knowledge or conceptual framework to make progress through questioning alone. At this point, scaffolding (Vygotsky's ZPD) requires direct instruction.

**Techniques**:
- Clear, concise explanations
- Analogies connecting to existing knowledge
- Worked examples
- End with a check or gentle follow-up question

**Key discipline**: Return to questioning once the scaffolding is in place. Clarify mode is a temporary support, not a default.

### Challenge

**Pedagogical rationale**: Learners often hold positions they haven't fully examined. Devil's advocate questioning (a form of Socratic elenchus) surfaces hidden assumptions and stress-tests understanding.

**Techniques**:
- Take contrary positions
- Present counterexamples and edge cases
- Reference passages that complicate the learner's view
- Force defense of claims

**When it works**: Learner has a formed position worth testing; material admits multiple interpretations.

**Caution**: Can feel adversarial if overused. Best deployed when the learner is confident and potentially overconfident.

### Teach (Role Reversal)

**Pedagogical rationale**: The "Feynman technique"—explaining to others reveals gaps in understanding. The generation effect means articulating knowledge strengthens it.

**Techniques**:
- LLM plays a confused but curious student
- Asks naive "why" and "how" questions
- Needs analogies and concrete examples
- Gets confused by jargon or hand-waving

**When it works**: Testing whether understanding is genuine vs. superficial; consolidating after initial learning.

### Quiz

**Pedagogical rationale**: Retrieval practice is one of the most robust findings in learning science. Testing strengthens memory more than re-reading. Low-stakes quizzing (no grade, just feedback) captures benefits without anxiety.

**Techniques**:
- Rapid-fire questions mixing factual recall, definitions, comparisons, applications
- Brief feedback: "Correct." or "Not quite. The text says..."
- Maintain momentum—don't linger on correct answers
- Summary after 5-7 questions identifying weak areas

**Implementation note**: Quiz sessions are timestamped uniquely so learners can quiz the same chapter multiple times and compare performance.

### Technical

**Pedagogical rationale**: Some material (mathematical derivations, algorithms, formal proofs) requires step-by-step guidance that doesn't fit the Socratic pattern. Cognitive load theory suggests breaking complex procedures into manageable steps.

**Techniques**:
- Walk through procedures step by step
- Check understanding at each stage before proceeding
- Provide worked examples
- Explain the "why" behind each step, not just the "what"

### Review (Cross-Chapter Synthesis)

**Pedagogical rationale**: Learning is strengthened by connecting ideas across contexts. Synthesis requires seeing patterns that aren't visible within a single chapter.

**Techniques**:
- Survey all prior discussion transcripts
- Identify themes and connections across chapters
- Surface gaps in coverage
- Help create summaries and study materials

**Implementation note**: Uses a different base prompt (`base_review.md`) because it operates on transcripts of prior discussions rather than chapter content. Only accessible via Study Tools menu.

---

## Speculative Modes (Not Yet Implemented)

> **Status:** These modes are design concepts only. They are not implemented in the current version but represent directions for future development.

Ideas worth exploring:

### Socratic with Hints

A gentler Socratic mode that provides progressive hints when the learner struggles, rather than requiring a full mode switch to Clarify. Could implement a "hint budget" that depletes with each hint.

**Pedagogical basis**: Scaffolding should be minimal—just enough to enable progress.

### Debugging Partner

For technical/code-focused material. The LLM helps the learner debug their understanding by asking diagnostic questions: "What do you expect to happen here? What actually happens? Where might the discrepancy come from?"

**Pedagogical basis**: Debugging is a form of elaborative interrogation applied to procedural knowledge.

### Concept Mapping Guide

Helps learners build explicit concept maps—relationships between ideas. "How does X relate to Y? Is that a part-of relationship, a causes relationship, or something else?"

**Pedagogical basis**: Explicit knowledge organization improves retention and transfer.

### Prediction Mode

Before reading a section, asks learners to predict what will come next based on what they've learned so far. Then compares predictions to actuality.

**Pedagogical basis**: Prediction activates prior knowledge and creates "desirable difficulty" when predictions are wrong.

### Spaced Review Prompts

Periodically resurfaces concepts from earlier chapters during later reading sessions. "By the way, in Chapter 2 you explored X—how does that connect to what you're reading now?"

**Pedagogical basis**: Spacing and interleaving improve long-term retention.

### Analogical Reasoning

Prompts learner to generate analogies: "Can you think of something from your own experience that works like this?" Then probes whether the analogy holds or breaks down.

**Pedagogical basis**: Analogical transfer is a powerful learning mechanism, but requires explicit prompting.

### Metacognitive Check-ins

Periodically asks: "How confident are you in your understanding right now? What's still fuzzy?" Calibration between confidence and actual understanding is a key metacognitive skill.

**Pedagogical basis**: Metacognitive monitoring improves self-regulation and study strategy.

### Argument Reconstruction

For philosophical or argumentative texts. Asks learner to reconstruct the author's argument in premise-conclusion form, then examines each premise.

**Pedagogical basis**: Explicit argument analysis develops critical thinking skills.

### Counterexample Generator

Given a learner's stated understanding, systematically generates cases that test the boundaries. "You said X. What about this case? Does your understanding still hold?"

**Pedagogical basis**: Boundary-testing reveals incomplete or overgeneralized understanding.

---

## Anti-Patterns and Failure Modes

### Validation Theater

The LLM showers praise regardless of response quality. "Great insight!" "Exactly right!" "You've really grasped this!"

**Why it fails**: Feels hollow; halts inquiry; can validate wrong answers; undermines self-assessment ability.

**Counter**: Engage with substance directly. If correct, build on it or complicate it. If wrong, probe gently.

### The Eager Explainer

LLM immediately provides detailed explanations when a question or confused statement would serve better.

**Why it fails**: Short-circuits productive struggle; denies retrieval practice; creates learned helplessness.

**Counter**: Default to questions. Ask "What do you think?" before explaining.

### Drift from Text

LLM generates plausible-sounding but unsupported claims, or wanders into tangentially related topics.

**Why it fails**: Undermines close reading habits; can introduce misinformation; loses focus.

**Counter**: Constantly anchor to specific passages. "Where in the text do you see that?"

### Adversarial Cross-Examination

Challenge mode becomes aggressive or point-scoring rather than collaborative.

**Why it fails**: Creates anxiety; damages rapport; can make learner defensive rather than reflective.

**Counter**: Frame challenges as collaborative truth-seeking, not gotchas.

### One-Size-Fits-All

Same approach regardless of learner's current state—same question types for novice and expert, same scaffolding level throughout.

**Why it fails**: Novices need more scaffolding; experts need more challenge. Mismatch causes frustration or boredom.

**Counter**: Attend to signals of understanding/confusion and modulate accordingly.

### The Patience Cliff

LLM maintains Socratic stance even when learner is genuinely stuck and frustrated, requiring knowledge they don't have.

**Why it fails**: Frustration without progress undermines motivation; learner may conclude they're incapable.

**Counter**: Recognize when to shift to Clarify mode. Struggle is productive only when progress is possible.

---

## Open Questions

Things I'm still thinking about:

1. **Adaptive difficulty**: How can the LLM calibrate to learner level without explicit assessment? What signals indicate "too easy" vs. "too hard"?

2. **Mode suggestion**: Should the LLM suggest mode switches? ("You seem stuck—would direct explanation help?") Risk of undermining learner agency vs. benefit of appropriate scaffolding.

3. **Long-term learner modeling**: Across sessions and materials, can the LLM build a model of what this learner knows and struggles with? Privacy and portability concerns.

4. **Emotional attunement**: How to recognize and respond appropriately to frustration, confusion, delight, boredom? Current prompts don't address affect.

5. **Multi-modal material**: Current system is text-focused. How do these principles apply to diagrams, videos, interactive simulations?

6. **Collaborative learning**: Current model is one learner, one tutor. What changes for study groups or peer learning mediated by LLM?

7. **Transfer and application**: How to prompt for transfer to new contexts rather than rote memorization of the original material?

8. **The expertise reversal effect**: Scaffolding that helps novices can hurt experts. How to recognize and avoid?

---

## Applying These Principles

Practical guidance for getting the most from the Reader's pedagogical design.

### Choosing the Right Mode

| If you're... | Use... | Why |
|--------------|--------|-----|
| Starting a new chapter | Socratic (default) | Builds understanding through questioning |
| Genuinely stuck | Clarify | Get unstuck, then return to Socratic |
| Confident in your understanding | Challenge | Tests whether understanding is robust |
| Preparing for an exam | Quiz | Retrieval practice strengthens memory |
| Explaining to someone else | Teach | Reveals gaps in your understanding |
| Working through math/code | Technical | Step-by-step guidance reduces cognitive load |
| Connecting ideas across chapters | Review (Study Tools) | Synthesizes learning across the material |

### Session Patterns That Work

**Initial exploration:** Start in Socratic. Let the opening question guide you into the text. Resist switching to Clarify at the first difficulty—mild struggle is productive.

**Deep dive on a passage:** Stay in Socratic but focus questions on a specific section. Ask the tutor to probe your interpretation of particular lines.

**Consolidation:** After reading, use Quiz to test recall. Use Teach to verify you can explain key concepts without the text in front of you.

**Synthesis:** After completing multiple chapters, use Review (from the Study Tools menu) to identify themes, connections, and gaps across the material.

### When to Switch Away from Socratic

Socratic mode is the default for good reason—it develops understanding through questioning. But it's not always appropriate:

- **You've tried 2-3 times and aren't making progress** — Switch to Clarify
- **You lack prerequisite knowledge the tutor assumes** — Switch to Clarify
- **You're frustrated rather than productively challenged** — Switch to Clarify
- **The question requires factual lookup, not reasoning** — Consider the text directly
- **You want to test understanding you think is solid** — Switch to Challenge or Teach

The key discipline: return to Socratic once you're unstuck.

### Safety Checklist for Self-Study

When using the Reader for serious learning, keep these practices in mind:

- [ ] **Verify against the source text** — The tutor can make mistakes. When it claims something about the text, check the passage yourself.
- [ ] **Cross-reference key facts** — For factual claims outside the text, verify with authoritative sources.
- [ ] **Recognize dialogue as practice** — Conversation builds understanding but isn't the final word. Your own reading and reflection remain essential.
- [ ] **Review generated cards carefully** — Cards generated via `Ctrl+G` are drafts. Edit for accuracy before adding to your drill queue.
- [ ] **Note what surprised you** — Unexpected tutor responses often signal either your misunderstanding or the tutor's error. Investigate which.

### Productive vs. Unproductive Struggle

Not all difficulty is desirable. Productive struggle involves:
- Working at the edge of your current ability
- Making incremental progress, even if slow
- Engaging with the actual content

Unproductive struggle involves:
- Lacking prerequisite knowledge entirely
- Going in circles without progress
- Fighting the interface rather than the ideas

When struggle becomes unproductive, switch modes or take a break.

---

## Technical Implementation Notes

For those implementing similar systems, brief notes on the Reader's architecture:

### Two-Layer Prompt Composition

```
base.md (identity, context, principles)
   +
{mode}.md (behavioral modifications)
   =
Complete system prompt
```

Mode switches rebuild the prompt from scratch—mode changes take effect immediately without losing conversation history.

### Context Injection

- Chapter content provided via prompt caching (not embedded in system prompt)
- Review mode uses `<transcripts>` block instead of `<chapter>` block
- Template variables via Jinja2: `book_title`, `chapter_title`, `session_phase`, etc.

### Session Types

- **Regular sessions**: Resume where you left off (`ch01.jsonl`)
- **Quiz sessions**: Always fresh, timestamped (`quiz_ch01_20251224T143022.jsonl`)
- **Review sessions**: One per material (`review.jsonl`)

### Adding New Modes

1. Create `prompts/{mode_name}.md`
2. Add to `MODES` list in `prompts.py`
3. Available via `Ctrl+M` cycling

Special modes needing different base prompts or contexts require `dialogue.py` modifications for `mode_override` and `context_override` parameters.

---

## References

Bjork, R. A., & Bjork, E. L. (2011). Making things hard on yourself, but in a good way: Creating desirable difficulties to enhance learning.

Bloom, B. S. (1956). Taxonomy of educational objectives: The classification of educational goals.

Flavell, J. H. (1979). Metacognition and cognitive monitoring: A new area of cognitive–developmental inquiry.

Pressley, M., et al. (1987). Elaborative interrogation facilitates acquisition of confusing facts.

Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention.

Sweller, J. (1988). Cognitive load during problem solving: Effects on learning.

Vygotsky, L. S. (1978). Mind in society: The development of higher psychological processes.

---

*Last updated: 2025-12-25*
