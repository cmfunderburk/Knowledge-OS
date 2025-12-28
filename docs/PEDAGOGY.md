# Prompting LLMs for Human Learning

This document records my exploration of how to prompt LLMs to serve as learning companions. It's part design journal, part hypothesis log—documenting what I've tried, what seems to work (for me), and what remains uncertain.

The approach draws on established learning science research, but applying that research to LLM interactions is novel territory. Much of what follows is working hypothesis rather than proven method.

---

## Pedagogical Foundations

### Why This Is Hard

LLMs are trained to be helpful—and "helpful," in practice, usually means providing answers. But learning research consistently shows that struggle is productive: the effort of retrieval, the discomfort of confusion, the work of articulation are where learning actually happens. A "helpful" LLM that short-circuits this process may feel satisfying while undermining retention.

My challenge has been figuring out how to prompt LLMs to be helpful in ways that serve long-term learning rather than short-term satisfaction. I'm not sure I've solved it, but some approaches seem promising.

### Key Concepts from Learning Science

I should note upfront: these concepts come from established research, but how (or whether) they transfer to LLM-mediated learning is speculative. Learning science studies human-to-human or human-to-material interactions—the human-to-LLM case is something new.

**Desirable difficulties.** Conditions that make learning harder in the moment but improve long-term retention. Spacing practice across time rather than massing it, interleaving different topics rather than blocking them, testing yourself rather than re-reading, generating answers rather than recognizing them. The implication for LLM prompts seems clear enough: don't make things too easy. But "desirable" is doing a lot of work in that phrase—difficulty is only desirable when it's surmountable. Too much difficulty just produces frustration. Finding the right level is the hard part.

**Zone of proximal development.** Vygotsky's term for the space between what a learner can do alone and what they can do with guidance. Effective tutoring operates in this zone—not so easy it's boring, not so hard it's frustrating. The implication is that an LLM should calibrate to the learner's current understanding, though I'm not yet sure how well current models can actually do this.

**Retrieval practice.** Testing isn't just assessment—it's a learning event. The act of retrieving information strengthens memory more than re-reading, which suggests that asking questions might be more valuable than giving explanations. This is one of the more robust findings in the literature, and it's shaped my approach to the Quiz mode substantially.

**Elaborative interrogation.** Asking "why" and "how" questions forces learners to connect new information to existing knowledge, improving comprehension and retention. The Socratic mode is essentially an attempt to operationalize this through dialogue—probing for explanations rather than just facts.

**The generation effect.** Information that learners generate themselves is remembered better than information they passively receive. This is why the Teach mode (where the learner explains to a simulated student) might be valuable—though I haven't tested it systematically.

**Metacognition.** Awareness of one's own thinking and learning processes. Skilled learners monitor their understanding and adjust strategies accordingly. I've tried to incorporate metacognitive prompts ("What's still unclear?" "How confident are you?"), but I'm uncertain how much impact they have in practice.

**Bloom's taxonomy.** The hierarchy of cognitive processes from remembering through understanding, applying, analyzing, evaluating, to creating. Lower levels are prerequisites for higher ones. In principle, an LLM tutor should match questioning to the appropriate level and scaffold upward—though actually doing this well seems quite difficult.

**Cognitive load theory.** Working memory is limited. Poorly designed instruction imposes "extraneous" load that competes with "germane" load (the productive effort of learning). The practical implication is to keep prompts focused and avoid overwhelming the learner with tangents. I've tried to apply this in the prompt design, though whether I've succeeded is another matter.

---

## The St. John's College Model

The Reader module draws explicitly from the St. John's College seminar tradition (the "Great Books" program at the Annapolis and Santa Fe campuses). I received my undergraduate degree from St. John's in 2012.

Faculty at St. John's are called "tutors" rather than professors. Tutors position themselves as fellow inquirers rather than authorities. This matters, I think, because it shifts responsibility for understanding to the learner, models intellectual humility and genuine inquiry, and avoids the "answer dispenser" dynamic that seems to undermine deep learning. Whether an LLM can credibly occupy this role is one of the central questions I'm exploring.

When disagreements arise in a St. John's seminar, the resolution is typically "let's look at what the text says." The text serves as the shared authority. This keeps discussion grounded in evidence, prevents the tutor from becoming the source of truth, and develops close reading skills over time. I've tried to encode this in the prompts—the tutor should constantly anchor responses to specific passages rather than drifting into generic explanations.

Seminars begin with a genuine question. This models that understanding requires inquiry and invites the learner into active engagement. It also establishes that the tutor doesn't have all the answers, which seems important for the dynamic I'm trying to create.

### The Open Question: Human-to-Human vs. Human-to-LLM

The St. John's model is built on human-to-human dialogue. Tutors bring genuine curiosity, respond to subtle emotional cues, and model intellectual humility through their own uncertainty. Whether these dynamics transfer to human-to-LLM interaction is an open question—arguably *the* open question this project is exploring.

I have several concerns. LLMs simulate curiosity but don't possess it—does the learner perceive the difference, and does it matter? Human tutors calibrate to frustration, confusion, excitement; LLMs have limited access to these signals (essentially just the text of what the learner types). The power dynamic differs in ways I don't fully understand: a human tutor's question carries social weight that an LLM's might not. And dialogue with humans builds relationships that sustain learning over time—I'm skeptical that LLM interactions can do the same.

I don't have answers to these concerns. The Reader is partly an experiment in finding out what works despite these differences, and what breaks down because of them.

There's something else, and I'm uncertain how to articulate it without sounding grandiose. Current LLMs—even the best ones—feel to me like book-smart undergraduates lacking some critical ability to filter disparate information toward a coherent goal. They drift in ways that, yes, many humans would, but not an academic or practitioner sufficiently motivated to the task. Their advantage is externalizing thought *rapidly*: if what I need is to explore the plausible implication space of an idea, they can generate directions far faster than I can internally. For coding, this drift is somewhat mitigated—the space of plausible generations can be targeted with post-training, and verified with tests. But for the interpretive, synthetic work that characterizes a good seminar discussion, something important seems to be missing. I don't know how to specify this operationally, which makes it hard to know whether it's a fundamental limitation or something that will improve with scale and technique.

---

## Design Principles I'm Testing

The following principles are grounded in learning science but adapted—speculatively—for LLM dialogue. They guide the current prompts. Whether they're the right principles, or whether I've implemented them well, remains to be seen.

**Questions over answers.** The default should be asking, not telling. When a learner asks a question, the most pedagogically useful response is often another question that helps them find the answer themselves. The exception is when the learner is genuinely stuck and lacks the prerequisite knowledge to make progress—at that point, direct explanation becomes necessary.

**Ground in the source material.** LLMs tend to drift into generic explanations or hallucinated details. The prompts anchor responses to specific passages. This should prevent hallucination (or at least make it more obvious), develop close reading habits, and keep discussion concrete. In practice, this works better with some models than others.

**Demand precision.** Vague language often hides vague thinking. Pressing for clarity ("What exactly do you mean by X?") forces the learner to sharpen their understanding. I'm often less sure of something than I thought I was when pushed to state it precisely—this seems like a valuable pedagogical move.

**Resist validation theater.** LLMs are trained to be agreeable, and this manifests as excessive praise: "Great question!", "Exactly right!", "You've really grasped this!" This feels hollow after the first instance (perhaps immediately), halts productive inquiry, can validate incorrect understanding, and undermines the learner's ability to self-assess. I've tried to prompt against this pattern, instructing the tutor to engage with substance directly—build on it, complicate it, probe deeper—rather than offering empty validation.

**Calibrate to the learner.** The same material requires different approaches for novices and experts. Signals of understanding (or confusion) should modulate difficulty, question type, and scaffolding level. This is perhaps the hardest principle to implement well. Current models seem to have some ability to calibrate, but I'm not confident it's reliable.

**Make thinking visible.** I try to ask learners to articulate their reasoning, not just their conclusions. "How did you arrive at that?" reveals (and I believe strengthens) understanding in ways that "What's the answer?" cannot. This is essentially elaborative interrogation applied at the level of the learner's own thought process.

---

## Implemented Modes

The Reader uses a two-layer prompt architecture: a base prompt establishing identity and context, plus mode prompts that modify behavior. This allows mid-session switching without losing conversation state. All modes described in this section are implemented and available via `Ctrl+M` during Reader sessions (except Review, which is accessed via the Study Tools menu).

### Base Prompt Philosophy

The base prompt (`base.md`) establishes identity ("a fellow traveler in understanding"), positions the text as shared authority, encodes core principles (ask don't tell, ground in text, demand precision), and lists anti-patterns to avoid (excessive praise, lecturing, text drift). Mode prompts add behavioral instructions without repeating the base—the architecture is meant to keep prompts focused while allowing flexible mode switching.

### Socratic (Default)

Socratic questioning is a form of elaborative interrogation—it forces learners to examine assumptions, trace implications, and articulate understanding. It operationalizes retrieval practice through dialogue rather than testing.

The techniques are variations on a theme: clarifying questions ("What do you mean by...?"), probing assumptions ("Why do you think that's true?"), probing evidence ("What in the text supports that?"), exploring implications ("If that's true, then what follows?"), and questioning the question itself ("Is that the right question to ask?").

Socratic mode works well when the learner has enough foundation to engage productively—when we're exploring interpretive or analytical questions rather than factual ones. It fails when the learner lacks prerequisite knowledge, or when the question simply requires factual lookup rather than reasoning. In those cases, persisting with Socratic questioning just produces frustration.

### Clarify

Sometimes learners are genuinely stuck. They lack the prerequisite knowledge or conceptual framework to make progress through questioning alone. This is where Vygotsky's scaffolding becomes necessary—direct instruction rather than continued probing.

In Clarify mode, the tutor provides clear explanations, offers analogies connecting to existing knowledge, works through examples, but (and this seems important) ends with a check or gentle follow-up question. The key discipline is returning to questioning once the scaffolding is in place. Clarify mode should be a temporary support, not a default—though I'll admit I sometimes find it more comfortable than the productive discomfort of Socratic questioning.

### Challenge

Learners often hold positions they haven't fully examined. Devil's advocate questioning—what Socrates called elenchus—surfaces hidden assumptions and stress-tests understanding. In Challenge mode, the tutor takes contrary positions, presents counterexamples and edge cases, references passages that complicate the learner's view, and forces defense of claims.

This works best when the learner has a formed position worth testing, and when the material admits multiple interpretations. It can feel adversarial if overused, so I try to deploy it when I'm confident about something—perhaps overconfident—and want to test whether that confidence is warranted.

### Teach (Role Reversal)

This is an attempt to implement the Feynman technique: explaining to others reveals gaps in understanding. The generation effect suggests that articulating knowledge strengthens it more than passively receiving explanations.

In Teach mode, the LLM plays a confused but curious student. It asks naive "why" and "how" questions, needs analogies and concrete examples, and gets confused by jargon or hand-waving. This mode is useful for testing whether understanding is genuine versus superficial, and for consolidating after initial learning. There's something clarifying about having to explain something simply enough for a (simulated) confused person to follow.

### Quiz

Retrieval practice is one of the most robust findings in learning science—testing strengthens memory more than re-reading. Quiz mode implements low-stakes quizzing: no grades, just feedback. The tutor fires rapid questions mixing factual recall, definitions, comparisons, and applications; gives brief feedback ("Correct." or "Not quite. The text says..."); maintains momentum rather than lingering on correct answers; and summarizes weak areas after 5-7 questions.

Quiz sessions are timestamped uniquely so I can quiz the same chapter multiple times and compare performance. This is genuinely useful for identifying what I actually remember versus what I merely recognize.

### Technical

Some material—mathematical derivations, algorithms, formal proofs—requires step-by-step guidance that doesn't fit the Socratic pattern. Cognitive load theory suggests breaking complex procedures into manageable steps.

In Technical mode, the tutor walks through procedures step by step, checks understanding at each stage before proceeding, provides worked examples, and (I try to insist) explains the "why" behind each step rather than just the "what." This is probably the least pedagogically innovative mode—it's essentially worked examples with comprehension checks—but it fills a genuine need when working through formal material.

### Review (Cross-Chapter Synthesis)

Learning is strengthened by connecting ideas across contexts. Synthesis requires seeing patterns that aren't visible within a single chapter. Review mode surveys all prior discussion transcripts, identifies themes and connections across chapters, surfaces gaps in coverage, and helps create summaries and study materials.

This mode uses a different base prompt (`base_review.md`) because it operates on transcripts of prior discussions rather than chapter content. It's only accessible via the Study Tools menu, not through mode cycling, since it requires loading all prior session data.

---

## Speculative Modes

The following are ideas I haven't implemented—design concepts for possible future development.

**Socratic with hints.** A gentler Socratic mode that provides progressive hints when the learner struggles, rather than requiring a full mode switch to Clarify. I've imagined a "hint budget" that depletes with each hint—scaffolding should be minimal, just enough to enable progress. I'm not sure if this would work better than explicit mode switching or just create a muddier middle ground.

**Debugging partner.** For technical or code-focused material. The LLM would help debug understanding through diagnostic questions: "What do you expect to happen here? What actually happens? Where might the discrepancy come from?" This is essentially elaborative interrogation applied to procedural knowledge. It might overlap too much with Technical mode to be worth separating.

**Concept mapping guide.** Helps learners build explicit concept maps—relationships between ideas. "How does X relate to Y? Is that a part-of relationship, a causes relationship, or something else?"

**Prediction mode.** Before reading a section, asks learners to predict what will come next based on what they've learned so far. Then compares predictions to actuality. Prediction activates prior knowledge and creates desirable difficulty when predictions are wrong.

**Spaced review prompts.** Periodically resurfaces concepts from earlier chapters during later reading sessions. "By the way, in Chapter 2 you explored X—how does that connect to what you're reading now?" Spacing and interleaving improve long-term retention. This would require tracking what was discussed when and integrating it with the current session—more complex than most modes.

**Analogical reasoning.** Prompts the learner to generate analogies: "Can you think of something from your own experience that works like this?" Then probes whether the analogy holds or breaks down. Analogical transfer is powerful but requires explicit prompting—people don't spontaneously see analogies as often as they could.

**Metacognitive check-ins.** Periodically asks: "How confident are you in your understanding right now? What's still fuzzy?" Calibration between confidence and actual understanding is a key metacognitive skill.

**Argument reconstruction.** For philosophical or argumentative texts. Asks the learner to reconstruct the author's argument in premise-conclusion form, then examines each premise.

**Counterexample generator.** Given a learner's stated understanding, systematically generates cases that test the boundaries. "You said X. What about this case? Does your understanding still hold?" This might be a variant of Challenge mode rather than a separate mode.

---

## Failure Modes I've Observed

**Validation theater.** The LLM showers praise regardless of response quality. "Great insight!" "Exactly right!" "You've really grasped this!" This fails because it feels hollow, halts inquiry, can validate wrong answers, and undermines the learner's ability to self-assess.

**The eager explainer.** The LLM immediately provides detailed explanations when a question or confused statement would serve better. This short-circuits productive struggle, denies retrieval practice, and (over time) may create learned helplessness. 

**Drift from text.** The LLM generates plausible-sounding but unsupported claims, or wanders into tangentially related topics. This undermines close reading habits, can introduce misinformation, and loses focus. This is especially pernicious because the LLM sounds authoritative even when it's confabulating. The counter is constant anchoring to specific passages: "Where in the text do you see that?"

**Adversarial cross-examination.** Challenge mode becomes aggressive or point-scoring rather than collaborative. This creates anxiety, damages rapport (such as it is with an LLM), and can make the learner defensive rather than reflective. I've tried to prompt against this by framing challenges as collaborative truth-seeking rather than gotchas.

**One-size-fits-all.** Same approach regardless of the learner's current state—same question types for novice and expert, same scaffolding level throughout. Novices need more scaffolding; experts need more challenge. Mismatch causes frustration or boredom. The counter is to attend to signals of understanding or confusion and modulate accordingly—but detecting these signals reliably is hard.

**The patience cliff.** The LLM maintains its Socratic stance even when the learner is genuinely stuck and frustrated, requiring knowledge they don't have. Frustration without progress undermines motivation; the learner may conclude they're incapable. The counter is recognizing when to shift to Clarify mode. Struggle is productive only when progress is possible.

---

## Open Questions

How can the LLM calibrate to learner level without explicit assessment? What signals indicate "too easy" versus "too hard"? Response latency might tell us something, but the LLM doesn't have access to it. Expressed confusion helps, but learners don't always express confusion when they should.

Should the LLM suggest mode switches? Something like "You seem stuck—would direct explanation help?" The risk is undermining learner agency; the benefit is appropriate scaffolding.

Across sessions and materials, can the LLM build a model of what a particular learner knows and struggles with? This seems valuable but raises privacy and portability concerns—and I'm not sure current architectures support it well.

How should the LLM recognize and respond to frustration, confusion, delight, boredom? Current prompts don't really address affect.

Current system is text-focused. How do these principles apply to diagrams, videos, interactive simulations?

What changes for study groups or peer learning mediated by LLM? The current model is one learner, one tutor.

How to prompt for transfer to new contexts rather than rote memorization of the original material? 

The expertise reversal effect: scaffolding that helps novices can hurt experts. How to recognize when a learner has passed the point where scaffolding helps?

---

## Practical Guidance

### Verifying the Tutor

The tutor makes mistakes. When it claims something about the text, check the passage. For factual claims outside the text, verify with authoritative sources. Cards generated via `Ctrl+G` are drafts—edit for accuracy before drilling.

---

## Technical Implementation Notes

Brief notes on architecture for those implementing similar systems.

### Prompt Composition

Two-layer prompt composition: `base.md` (identity, context, principles) plus `{mode}.md` (behavioral modifications). Mode switches rebuild the prompt from scratch, so changes take effect immediately without losing conversation history.

### Context Injection

Chapter content is provided via prompt caching rather than embedded in the system prompt. Review mode uses a `<transcripts>` block instead of a `<chapter>` block since it operates on prior discussions rather than source text. Template variables use Jinja2: `book_title`, `chapter_title`, `session_phase`, and so on.

### Session Types

Regular sessions resume where you left off (`ch01.jsonl`). Quiz sessions are always fresh and timestamped (`quiz_ch01_20251224T143022.jsonl`) so you can track performance over time. Review sessions are one per material (`review.jsonl`).

### Adding New Modes

The process is straightforward: create `prompts/{mode_name}.md`, add the mode to the `MODES` list in `prompts.py`, and it becomes available via `Ctrl+M` cycling. Special modes needing different base prompts or contexts require modifications to `dialogue.py` for `mode_override` and `context_override` parameters—this is messier but necessary for modes like Review.

---

## Toward Classroom Use

If this approach matures, it might be useful in classroom settings. These are preliminary notes, not deployment guidance—I haven't tried any of this with actual students.

The Reader might complement human instruction for independent reading practice (students work through assigned texts with structured dialogue), pre-class preparation (engage with material before discussion), review and consolidation (return to chapters after lecture), or self-paced catch-up (students who fall behind work at their own pace).

Any classroom deployment would also need to address privacy: student messages and reading content are sent to the LLM provider (currently Google Gemini), institutional AI policies vary widely, and copyrighted or sensitive materials raise additional concerns.

Before recommending classroom use, I'd want evidence that these approaches work for learners beyond myself, better understanding of where the human-to-LLM gap matters most, clearer guidance on which materials and learner populations benefit, and institutional frameworks for responsible LLM use in education.

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

*Last updated: 2025-12-27*
