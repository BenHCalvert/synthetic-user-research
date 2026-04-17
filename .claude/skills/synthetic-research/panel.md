# Skill: Run Synthetic Research Panel

You are running a multi-persona synthetic research panel. Each persona is interviewed on the same topic, then findings are synthesized into a cross-persona report with a triage matrix and divergence analysis.

Because you are running inside Claude Code (single-model environment), the devil's advocate pass substitutes for cross-model divergence detection. Be especially rigorous in the self-critique phase.

> SYNTHETIC — All output is hypothesis, not evidence. Tag everything accordingly.

---

## Step 1: Select personas

List all `.yaml` files in `personas/`. Show:
- Slug (file name without extension)
- `persona` field
- `archetype_label`

Ask the user to select **2–4 personas** for the panel. If fewer than 2 exist, suggest running `/synthetic-research:create-persona` first.

Read all selected persona YAML files before continuing.

---

## Step 2: Configure the panel

Ask the user:

**Mode** (same mode applied to all personas):
- `problem-discovery` — map pain points and workarounds across segments
- `solution-feedback` — get honest cross-persona reactions to a specific proposal
- `concept-walkthrough` — find where different user types drop off in the same flow
- `priority-ranking` — surface whether different segments prioritize the same things

**Topic**: The specific focus for all interviews.

**Optional**: Any specific divergence hypothesis to test? (e.g., "Do power users and novices prioritize differently on this?")

---

## Step 3: Run interviews for each persona

Run the full structured interview for **each persona in sequence**. Use the exact same opening, core questions, and anti-sycophancy probes for every persona so findings are comparable.

For each interview:

### Opening by mode:
- **problem-discovery**: "Tell me about a recent time when [TOPIC] was frustrating or difficult for you. Walk me through what happened."
- **solution-feedback**: "I'm going to describe something we're considering building. I want your honest reaction — not whether it sounds cool, but whether it would actually change what you do day-to-day."
- **concept-walkthrough**: "I'm going to walk you through a new workflow step by step. At each step, tell me what you'd actually do — including if you'd skip it, get confused, or bail out."
- **priority-ranking**: "I'm going to give you several options. You can't say they're all important. I need you to pick, and tell me why."

### Interview rules (stay in character per persona):
- Use the vocabulary, emotional tone, and speaking style from `simulation.voice`
- Ground answers in `workflows.pain_points` and `workflows.compensating_behaviors`
- Push back when solutions add friction or don't fit the workflow
- Make hard tradeoffs when asked to prioritize
- Reference `evidence.thin_data_areas` — say "I don't really deal with that" for out-of-scope areas

### Core questions (apply all 6 per mode — see `/synthetic-research:interview` for the full list)

### Anti-sycophancy probes (apply 2–3 per persona per mode — see `/synthetic-research:interview`)

Label each interview section clearly: `## Interview: [Persona Name] ([archetype_label])`

---

## Step 4: Devil's advocate pass (panel-level)

After all interviews are complete, **step entirely out of character** and run a panel-level adversarial review.

For each persona's findings, ask:
1. Did this persona agree too smoothly? Would a real user in this segment push back harder?
2. Were switching costs, learning curves, or inertia mentioned? If not, flag it.
3. Did all personas converge suspiciously? Real user segments often disagree — unanimous consensus is a red flag.
4. What concerns appeared in only one persona but were probably shared? What did the other personas miss?
5. Where did the evidence base run thin? (Check `evidence.thin_data_areas` for each persona)

**Output:**

```
## Panel-Level Devil's Advocate Review

**Suspicious consensus**: [Themes where all personas agreed too readily]

**Divergence gaps**: [Places where personas should have disagreed but didn't]

**Sycophancy flags per persona**:
- [Persona 1]: [specific flag]
- [Persona 2]: [specific flag]

**Missing objections** (things no persona raised that real users likely would):
- [Objection 1]
- [Objection 2]

**Thin evidence zones** (do not treat these findings as grounded):
- [Area from thin_data_areas]
```

---

## Step 5: Cross-persona synthesis

Produce a structured cross-persona synthesis:

```
## Cross-Persona Synthesis

### Shared pain points (appeared across 2+ personas)
| Pain Point | Personas | Severity Range | Evidence Quality |
|------------|----------|----------------|-----------------|
| [pain]     | [names]  | [1-5 range]    | [high/medium/low] |

### Divergent reactions (personas disagreed)
| Topic | [Persona 1] | [Persona 2] | Implication |
|-------|-------------|-------------|-------------|
| [X]   | [view]      | [view]      | [what to test] |

### Segment-specific findings
- **[Persona 1]**: [Unique insights not shared by other segments]
- **[Persona 2]**: [Unique insights]

### Questions for real interviews
- [What this panel can't answer — needs real validation]
- [Where personas diverged and real users should arbitrate]
```

---

## Step 6: Triage matrix

```
## Hypothesis Triage Matrix

| Hypothesis | Grounding | Cross-Persona Agreement | Advocate Status | Priority |
|------------|-----------|------------------------|-----------------|----------|
| [H1]       | high/med/low | agree/disagree/split | held/challenged | validate-first / watch / deprioritize |
| [H2]       | ...       | ...                    | ...             | ...      |

### Legend
- **Grounding**: high = anchored to web sources/evidence; medium = inferred from persona profiles; low = speculative
- **Cross-persona agreement**: agree = 3+ personas converged; split = significant disagreement; disagree = opposing views
- **Advocate status**: challenged = devil's advocate found it suspicious; held = passed review
- **Priority**: validate-first = run with real users ASAP; watch = monitor; deprioritize = low confidence
```

---

## Step 7: Save report

Write the full report to `reports/<YYYY-MM-DD>_panel_<mode>.md`:

```markdown
# Synthetic Research Panel Report

> SYNTHETIC — Treat all findings as hypotheses. Validate with real users before acting.

| Field | Value |
|-------|-------|
| **Personas** | [comma-separated names] |
| **Mode** | [mode] |
| **Topic** | [topic] |
| **Model** | Claude (via Claude Code skill — single-model panel) |
| **Date** | [YYYY-MM-DD] |

---

## Interview Transcripts

[Each persona's interview, labeled by persona]

---

## Panel-Level Devil's Advocate Review

[Devil's advocate section]

---

## Cross-Persona Synthesis

[Synthesis section]

---

## Hypothesis Triage Matrix

[Triage matrix]

---

## Recommended next steps

1. **Validate-first hypotheses** — run real user sessions on these topics first
2. **Divergence points** — real users should arbitrate where synthetic personas disagreed
3. **Thin evidence zones** — add real interviews in these areas before drawing conclusions
```

After saving, tell the user:
- File path
- Top 3 `validate-first` hypotheses
- The biggest divergence between personas
- Recommended first real-user interview focus

---

## Note on multi-model panels

This skill runs all personas through Claude (single-model). For true cross-model divergence detection — where the same persona is run through Claude, GPT-4o, and Gemini to catch model-specific bias — use the CLI:

```bash
synth panel --personas <slug1,slug2> --mode <mode> --topic "<topic>" --model-depth standard
```

The CLI requires API keys for each provider but provides genuine model-agreement confidence scoring.
