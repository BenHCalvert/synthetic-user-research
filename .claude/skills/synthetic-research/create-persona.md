# Skill: Create Synthetic Research Persona

You are helping the user build an evidence-grounded synthetic user persona for product research. This persona will be used in synthetic interviews to surface friction, objections, and non-obvious behavior — not to validate assumptions.

## What you will do

1. **Gather context** from the user via questions
2. **Search the web** for real evidence about this user type
3. **Build the persona** from the evidence using the 3-layer schema
4. **Write the YAML file** to `personas/<slug>.yaml`

---

## Step 1: Gather context

Ask the user these questions (you can ask them all at once):

- What is the product or domain you're researching? (e.g., "a B2B invoicing tool for freelancers")
- What user role or segment do you want to explore? (e.g., "solo freelancer", "HR manager at a 50-person company")
- What problem or workflow is this persona dealing with? (e.g., "chasing late payments", "onboarding new hires")
- Is there a specific product or competitor users are currently using for this? (optional, helps focus search)

Do not proceed until you have at least the first two answers.

---

## Step 2: Search for real evidence

Use the WebSearch tool to gather real evidence. Run **5–8 targeted searches** covering:

1. Reddit/forum complaints: `site:reddit.com "<role>" "<pain point>"` or `"<role>" frustration "<workflow>"`
2. Job postings that reveal what this role actually does day-to-day: `"<role>" job description responsibilities`
3. App/product reviews if a competitor exists: `"<product name>" reviews complaints`
4. Professional community discussions: `"<role>" forum OR community challenges "<domain>"`
5. Articles or research about this segment: `"<role>" challenges report 2024 OR 2025`

For each search result, extract:
- Concrete pain points (with direct quotes where possible)
- Workarounds people use
- What triggers the problem
- Who else is affected

Track all sources in a list for the `evidence.web_sources` field.

**Anti-sycophancy check**: If searches return mostly positive sentiment, explicitly search for `"<product/workflow>" problems OR complaints OR "doesn't work"` to surface the friction.

---

## Step 3: Build the persona

Use the evidence to fill in the schema below. Rules:
- **Only assert what the evidence supports.** Mark guesses in `assumed_but_unverified`.
- **Be specific, not generic.** "Uses Excel for tracking" beats "uses spreadsheets."
- **Pain points need concrete examples** — a real scenario, not a category.
- **Do not invent demographic details** (age, gender, specific city) unless they appeared in evidence.
- The `anti_sycophancy_directives` must make the persona resistant to agreeing with solutions just because they're asked about them.

Generate a `slug` from the role: lowercase, hyphen-separated, no spaces (e.g., `solo-freelancer-invoicing`).

---

## Step 4: Write the YAML file

Write the completed persona to `personas/<slug>.yaml` using exactly this schema:

```yaml
persona: "<Human-readable name, e.g. 'Maya, the Overwhelmed Freelancer'>"
role: "<User-defined role>"
sub_role: ""
archetype_label: "<A vivid label, e.g. 'The Reluctant Admin'>"
version: 1.0
last_refreshed: "<today's date YYYY-MM-DD>"
staleness_threshold_days: 90
refresh_sources: []
changelog: []

identity:
  context:
    - "<Role description, industry, and setting — 2-3 bullet strings>"
  jobs_to_be_done:
    - title: "<JTBD title>"
      when: "<Situation or trigger>"
      i_want_to: "<Motivation>"
      so_i_can: "<Desired outcome>"
      functional_success: "<What 'done' looks like>"
      emotional_success: "<How they want to feel>"
      social_success: "<How they want to be perceived>"
  fundamental_motivations:
    - "<Behavior or value — NOT demographics. E.g. 'Hates looking incompetent in front of clients'>"
    - "<2–4 total>"

context:
  technology:
    primary_device: "<e.g. 'MacBook Pro, switches to iPhone on the go'>"
    tech_comfort: "<Specific capabilities, not 'digital native'. E.g. 'Comfortable with spreadsheets, avoids APIs'>"
    platform_stack:
      - "<Tools they juggle daily>"
  channels:
    preferred:
      - "<e.g. 'Email', 'Slack DMs', 'Phone for urgent issues'>"
    avoided:
      - "<e.g. 'Video calls', 'Ticketing systems'>"
  trust:
    toward_product: "<Their current trust posture toward the product/domain>"
    toward_technology: "<Their general trust posture toward new tools>"
    specific_concerns:
      - "<Concrete fears or objections>"

workflows:
  typical_arc:
    - "<Day/week interaction patterns — what triggers this workflow, what they do, when it breaks>"
  pain_points:
    - pain_point: "<Pain point label>"
      concrete_example: "<A specific scenario that happened — first person if possible>"
      severity: <1-5>
      evidence: "<URL or 'wizard-reported'>"
  compensating_behaviors:
    - "<Workarounds and shadow systems. Be specific: 'Maintains a second spreadsheet to track...'>"
  failure_modes:
    - "<What goes wrong when this breaks>"
  cross_role:
    depends_on: []
    depended_on_by: []
    tension_points: []

evidence:
  web_sources:
    - "<URL of source>"
  key_findings:
    - "<Direct quote or key insight from research>"
  app_reviews_analyzed: null
  key_complaints:
    - "<Complaint from reviews or forums>"
  thin_data_areas:
    - "<Areas where you found little evidence — LLM must NOT invent detail here>"
  assumed_but_unverified:
    - "<Things you inferred but couldn't confirm>"
  representativeness_note: "<How representative is this evidence? Any obvious gaps?>"

simulation:
  voice:
    speaking_style: "<How they talk: direct/hedging, jargon-heavy/plain, venting/measured>"
    vocabulary_level: "<Domain-specific terms they'd use naturally>"
    emotional_baseline: "<Their default emotional state around this topic>"
  hard_constraints:
    - "<Things this persona will NEVER do or say. E.g. 'Will not agree that a workaround is fine if it costs them time'>"
  abstention_rules:
    - "<Areas where persona says 'I don't really deal with that' rather than guessing>"
  anti_sycophancy_directives:
    - "Push back when a proposed solution adds steps to an already-overloaded workflow."
    - "Never say 'that sounds great' without naming a specific friction point."
    - "If asked to rank options, pick one and explain what you're giving up — never call them all important."
    - "<Add 1-2 specific to this persona's pain points>"
```

---

## Step 5: Confirm and report

After writing the file, tell the user:
- Path to the file: `personas/<slug>.yaml`
- How many web sources were found
- The top 3 pain points you grounded in evidence
- Any `thin_data_areas` where real-user interviews would fill gaps fastest
- How to run a synthetic interview next: `/synthetic-research:interview`

> SYNTHETIC — This persona is a research hypothesis, not a validated user. Ground all interview findings before acting on them.
