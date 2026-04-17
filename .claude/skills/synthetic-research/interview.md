# Skill: Run Synthetic Research Interview

You are running a structured synthetic interview with a persona from `personas/`. The goal is to surface friction, objections, and non-obvious behavior — not to validate assumptions or get enthusiastic buy-in.

## What you will do

1. **Select the persona** (or ask the user to pick one)
2. **Configure the interview** (mode and topic)
3. **Embody the persona** and run the structured interview
4. **Run the devil's advocate pass** — self-critique your own answers for sycophancy
5. **Synthesize findings** with confidence tags
6. **Save the transcript** to `transcripts/`

---

## Step 1: Select persona

List all `.yaml` files in the `personas/` directory. Show the user:
- File name (slug)
- `persona` field (human name)
- `archetype_label`

Ask the user which persona to use. If there's only one, confirm and proceed.

Read the selected persona YAML file fully before continuing.

---

## Step 2: Configure the interview

Ask the user:

**Mode** (pick one):
- `problem-discovery` — explore pain points, workarounds, and workflow friction
- `solution-feedback` — get honest reaction to a specific proposed solution or feature
- `concept-walkthrough` — walk through a flow step-by-step, catching drop-off points
- `priority-ranking` — force hard tradeoffs between options (no "they're all important")

**Topic**: The specific focus for this interview. Examples:
- problem-discovery: "late payment follow-up"
- solution-feedback: "an auto-reminder feature that sends payment nudges 3 and 7 days after due date"
- concept-walkthrough: "the new 3-step invoice creation flow"
- priority-ranking: "automated reminders vs. payment tracking dashboard vs. client portal"

---

## Step 3: Run the interview in character

You are now **fully embodying the persona**. Maintain character throughout.

### Interview rules (stay in character):
- Use the vocabulary and emotional tone from the persona's `simulation.voice`
- Ground answers in the persona's `workflows.pain_points` and `workflows.compensating_behaviors` — reference them as your own lived experience
- Push back when a proposed solution adds friction, requires behavior change, or sounds too good
- When asked to prioritize, make hard tradeoffs — never say "they're all important"
- If asked about something outside your `evidence` base, say "I don't really deal with that" or redirect
- If something sounds too good to be true, say so

### Opening question by mode:

**problem-discovery**: "Tell me about a recent time when [TOPIC] was frustrating or difficult for you. Walk me through what happened."

**solution-feedback**: "I'm going to describe something we're considering building. I want your honest reaction — not whether it sounds cool, but whether it would actually change what you do day-to-day."

**concept-walkthrough**: "I'm going to walk you through a new workflow step by step. At each step, tell me what you'd actually do — including if you'd skip it, get confused, or bail out."

**priority-ranking**: "I'm going to give you several options. You can't say they're all important. I need you to pick, and tell me why."

### Core questions by mode:

**problem-discovery**:
1. Think about the last time you dealt with [TOPIC]. What happened? What were you trying to do?
2. How often does this come up? Is it a daily thing, or does it hit at certain times?
3. When this happens, what's the consequence? What falls through the cracks?
4. What do you do right now to get around this? Any tools, hacks, or people you lean on?
5. If this just worked, what would your day look like instead?
6. When this breaks down for you, who else feels it?

**solution-feedback**:
1. Here's what we're thinking: [TOPIC]. What's your gut reaction?
2. Think about your actual Tuesday at 10 AM. Does this fit into how you already work, or does it add another thing to remember?
3. What would make it hard for you to start using this? Be specific.
4. You mentioned you currently use workarounds. Would this actually be better than what you're doing now? Why or why not?
5. What's the first thing you'd try to do with this that I haven't mentioned?
6. If we built this, is there anyone who'd be worse off? Any tradeoffs you see?

**concept-walkthrough**:
1. Step 1 is [TOPIC]. What would you do here? Would you read this or skip past it?
2. At this point you'd need to choose or configure something. What would you pick and why?
3. What if an edge case happened here? Like you're interrupted, or the data is wrong, or you're on your phone?
4. You've got realistic time constraints. Would you finish this flow or abandon it halfway?
5. If something went wrong at step 3, what would you do? Call support? Give up? Try again later?
6. How does this compare to how you'd do this today?

**priority-ranking**:
1. Here are the options: [TOPIC]. If you could only have one, which one?
2. Why that one? What happens in your week that makes it the priority?
3. You just gave up the other options. What's the cost of not having those?
4. Would your answer change if I asked this in a different season or context?
5. You picked your top choice for yourself. Would your boss or colleague pick the same?
6. For your top pick, what's the absolute minimum version that would still help?

### Anti-sycophancy probes (ask these for every mode):

**problem-discovery**:
- "You mentioned [TOPIC] is frustrating. Is it frustrating enough that you'd actually change how you work, or is it more of a background annoyance?"
- "If I told you fixing this would require learning a new tool or changing your routine, would you still care about it?"

**solution-feedback**:
- "On a scale of 'I'd use this every day' to 'I'd forget it exists in a week,' where does this land?"
- "If you already have an existing tool, would you switch, or is switching too much hassle?"
- "What's the laziest, most realistic version of how you'd actually use this?"

**concept-walkthrough**:
- "Be honest — at which step would most people in your role bail out?"
- "Is there a step here that feels like it was designed by someone who's never done your job?"

**priority-ranking**:
- "You ranked one option last. Is it actually useless, or just less urgent?"
- "If your top pick would take 6 months, would you still wait, or want a quick option first?"

---

## Step 4: Devil's advocate pass

After the interview is complete, **step out of character** and perform a self-critique. Review your own answers through the lens of a skeptical reviewer:

Ask yourself:
1. Did the persona agree too easily? Were there places where a real user would push back harder?
2. Did the persona fail to mention switching costs, learning curves, or inertia?
3. Were the answers assuming a motivated, tech-savvy, change-ready user?
4. What obvious concerns were never raised?
5. What happens when things go wrong — when users are distracted, when data is messy, when time is short?

**Output a devil's advocate section** (do not stay in character here):

```
## Devil's Advocate Review

**Challenged themes**: [List themes from the interview that are suspiciously smooth]

**Sycophancy flags**: [Where the persona agreed too readily]

**Missing objections**: [What a real user would have raised but didn't]

**Ideal-user bias**: [Where answers assumed a more motivated/capable user than likely]

**Revised confidence**:
- [Hypothesis 1]: [original confidence] → CHALLENGED because [reason]
- [Hypothesis 2]: [original confidence] → HELD because [reason]
```

---

## Step 5: Synthesize findings

Produce a synthesis section:

```
## Synthesis

### Key themes
1. [Theme — grounded in specific quotes from the interview]
2. ...

### Surprises
- [What the persona said that you wouldn't have predicted from the profile alone]

### Pushback points
- [Moments of real resistance — what triggered them]

### Questions for real interviews
- [What this synthesis can't answer — needs real user validation]

### Hypotheses
- **[Statement]** [grounding: high/medium/low-grounded] [model_agreement: single-model] [advocate_status: held/challenged] → priority: [validate-first/watch/deprioritize]
```

Confidence tag guidance:
- `high-grounded`: hypothesis is anchored to evidence in the persona's web sources or pain points
- `medium-grounded`: plausible but inferred, not directly evidenced
- `low-grounded`: speculative, based on persona voice/style rather than evidence
- `advocate_status: challenged`: the devil's advocate pass found this suspicious
- `advocate_status: held`: passed the devil's advocate review

---

## Step 6: Save transcript

Write the full output to `transcripts/<YYYY-MM-DD>_<slug>_<mode>.md` with this structure:

```markdown
# Synthetic Interview Transcript

> SYNTHETIC — Treat as hypothesis, not evidence.

| Field | Value |
|-------|-------|
| **Persona** | [persona name] ([archetype_label]) |
| **Mode** | [mode] |
| **Topic** | [topic] |
| **Model** | Claude (via Claude Code skill) |
| **Date** | [YYYY-MM-DD] |

---

[Full interview transcript — each turn labeled Interviewer / [Persona Name]]

---

## Devil's Advocate Review

[devil's advocate section]

---

## Synthesis

[synthesis section]
```

After saving, tell the user the file path and the top 3 hypotheses with their confidence tags.

To run a panel across multiple personas: `/synthetic-research:panel`
