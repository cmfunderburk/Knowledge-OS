# Introduction to KnOS

This document is for someone who has encountered KnOS and wants to understand what it is, whether it might be useful for them, and how to orient themselves in the documentation. It sits between the README's elevator pitch and the detailed guides, offering context that neither quite provides.

## What This Is (and Isn't)

KnOS is a personal study system built around two ideas: that understanding deepens through dialogue, and that knowledge persists through spaced retrieval. The first idea comes from the St. John's College tradition of seminar-based learning; the second from the cognitive science of memory. The software is an attempt to combine them into something useful for self-directed study.

The system has two core components:

**The Reader** is an LLM-powered reading companion. You load a book or paper, read a section, and then discuss it with the tutor. The tutor's default mode is Socratic—it asks questions rather than explains, trying to help you articulate your understanding rather than giving you someone else's. Other modes are available (Challenge, Clarify, Teach, Technical), and you can switch between them as the conversation demands.

**The Reviewer** is a spaced-repetition drilling system. Cards are markdown files with fenced code blocks that you reconstruct line-by-line. The scheduling uses Leitner boxes: perfect recall advances a card to longer intervals; any failure resets it to daily review. This is stricter than most spaced repetition systems—the idea is that partial recall indicates incomplete encoding, which merits revisiting.

The two components connect through a workflow: insights from reading sessions become drill cards, and drilling maintains what dialogue helped you understand. But they can also be used independently. Someone might use only the Reader for working through difficult texts, or only the Reviewer for maintaining technical knowledge.

What this is *not*: a replacement for reading, a way to avoid struggle, or a system that will work without active engagement. The Reader won't summarize books for you—it assumes you've read the passage and wants to discuss what you made of it. The Reviewer won't let you coast on partial knowledge—it demands exact reconstruction. Both require more effort than passive alternatives. The bet is that the effort pays off in understanding and retention.

## Who This Might Be For

I built this for my own study, so it reflects my particular situation: working through texts independently, without classroom structure, wanting both dialogue and long-term retention. But several profiles seem like reasonable fits:

**Self-directed readers of difficult texts.** If you work through philosophy, literature, history, or theory on your own, you may have noticed that reading without discussion leaves understanding shallow. The Reader provides a discussion partner who has read the text and can ask probing questions. This is not the same as a human seminar—I discuss the differences and limitations in [PEDAGOGY.md](PEDAGOGY.md)—but it appears to help with articulation and depth.

**Students preparing for exams or qualifying tests.** The Reviewer is designed for material you need to reproduce exactly: proofs, algorithms, definitions, formulas. The strict scoring means you can't fool yourself about whether you know something. The Leitner scheduling handles the timing problem of when to revisit what.

**Practitioners acquiring specialized knowledge.** Papers, textbooks, reference material—the Reader can help you work through dense content, and the Reviewer can help you retain the results. The system handles PDFs, EPUBs, and single-article papers.

**People skeptical of passive learning tools.** If flashcard apps feel too passive and ChatGPT conversations feel too aimless, this might offer a middle ground. The modes are designed to maintain productive difficulty: Socratic mode asks questions you can't easily deflect; Challenge mode argues against your interpretations; the Reviewer demands exact recall rather than vague recognition.

Whether this is actually useful for you depends on how you learn and what you're learning. I'd suggest trying a single session with one of the bundled classics—Aristotle, Cervantes, or Dostoevsky—before committing to setup with your own materials.

## How the Pieces Fit Together

A typical workflow might look like this:

1. **Read** a chapter of something you're working through.
2. **Open the Reader** and discuss the chapter. The tutor asks what you found significant, what you found unclear, how this connects to earlier material. You articulate your understanding; the tutor probes for precision and coherence.
3. **Identify key insights** from the dialogue—a distinction you hadn't noticed, a definition you want to retain, an argument structure you want to internalize.
4. **Create drill cards** capturing those insights. For technical material, this might be a code block with an algorithm. For conceptual material, it might be a `slots` block with prompts and answers.
5. **Drill due cards** daily. The Reviewer surfaces cards that need review and schedules future reviews based on your performance.

The Reader also has modes that support this workflow directly:
- **Quiz mode** tests your recall of a chapter's content through generated questions.
- **Review mode** synthesizes material across chapters, helping you see connections.
- Both generate potential drill card content you can promote to your deck.

But this is just one workflow. You might use only the Reader for exploratory reading with no intent to retain. You might use only the Reviewer for material you've learned elsewhere. The system doesn't enforce a particular pattern.

## Orienting in the Documentation

The documentation is organized by purpose:

| If you want to... | Start here |
|-------------------|------------|
| Understand the philosophy | [README.md](../README.md) |
| Install and run your first session | [GETTING_STARTED.md](GETTING_STARTED.md) |
| Learn commands, keybindings, formats | [USAGE.md](USAGE.md) |
| Understand the pedagogical design | [PEDAGOGY.md](PEDAGOGY.md) |
| Fix something that's broken | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Learn Reader-specific features | [knos/reader/OVERVIEW.md](../knos/reader/OVERVIEW.md) |
| Learn the drill card format | [solutions/examples/README.md](../solutions/examples/README.md) |

If you're evaluating whether to use this, I'd suggest reading the README first, then skimming PEDAGOGY.md to see if the approach resonates. If you decide to try it, GETTING_STARTED.md will get you running in about ten minutes.

## Setting Expectations

A few notes on what to expect:

**The LLM is not infallible.** Gemini (the default provider) sometimes hallucinates, misremembers text details, or drifts into generic advice. The PEDAGOGY document discusses this at length. The short version: treat the tutor as a well-read but sometimes unreliable interlocutor. When it claims something about the text, verify against the text.

**Dialogue takes time.** A productive reading session might take 20-40 minutes for a chapter you've read. This is not a tool for speeding through material. It's a tool for slowing down and engaging more deeply with material that merits it.

**Spaced repetition is uncomfortable.** The Reviewer will show you, repeatedly, that you don't know things as well as you thought. The 100%-or-reset policy means you'll see cards more often than in gentler systems. This is by design—the research on desirable difficulties suggests that some discomfort is productive—but it can feel frustrating.

**The system requires maintenance.** Cards need to be created, materials need to be registered, sessions accumulate. This is a tool for people who don't mind some administrative overhead in exchange for long-term utility.

## What's Next

If you want to try it:

1. Follow [GETTING_STARTED.md](GETTING_STARTED.md) to install and configure.
2. Run `uv run knos read` and select one of the bundled classics.
3. Read a section of the text, then discuss it with the tutor.
4. If the experience seems useful, add your own materials following the guides in USAGE.md.

If you want to understand the design before trying it, [PEDAGOGY.md](PEDAGOGY.md) explains the learning science and design choices in detail.
