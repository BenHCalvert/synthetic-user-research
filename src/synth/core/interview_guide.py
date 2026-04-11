"""Interview question bank for all four modes."""

INTERVIEW_GUIDES: dict[str, dict[str, str | list[str]]] = {
    "problem-discovery": {
        "opening": (
            "Tell me about a recent time when {topic} was frustrating or difficult "
            "for you. Walk me through what happened."
        ),
        "core_questions": [
            "Think about the last time you dealt with {topic}. What happened? What were you trying to do?",
            "How often does this come up? Is it a daily thing, or does it hit at certain times?",
            "When this happens, what's the consequence? What falls through the cracks?",
            "What do you do right now to get around this? Any tools, hacks, or people you lean on?",
            "If this just worked, what would your day look like instead?",
            "When this breaks down for you, who else feels it?",
        ],
        "anti_sycophancy_probes": [
            "You mentioned {topic} is frustrating. Is it frustrating enough that you'd actually change how you work, or is it more of a background annoyance?",
            "If I told you fixing this would require learning a new tool or changing your routine, would you still care about it?",
        ],
        "surprise_seekers": [
            "Is there anything about {topic} that works well that people don't talk about?",
            "What would make this problem worse, not better?",
        ],
    },
    "solution-feedback": {
        "opening": (
            "I'm going to describe something we're considering building. I want your "
            "honest reaction -- not whether it sounds cool, but whether it would "
            "actually change what you do day-to-day."
        ),
        "core_questions": [
            "Here's what we're thinking: {topic}. What's your gut reaction?",
            "Think about your actual Tuesday at 10 AM. Does this fit into how you already work, or does it add another thing to remember?",
            "What would make it hard for you to start using this? Be specific.",
            "You mentioned you currently use workarounds. Would this actually be better than what you're doing now? Why or why not?",
            "What's the first thing you'd try to do with this that I haven't mentioned?",
            "If we built this, is there anyone who'd be worse off? Any tradeoffs you see?",
        ],
        "anti_sycophancy_probes": [
            "On a scale of 'I'd use this every day' to 'I'd forget it exists in a week,' where does this land?",
            "If you already have an existing tool, would you switch, or is switching too much hassle?",
            "What's the laziest, most realistic version of how you'd actually use this?",
        ],
        "surprise_seekers": [
            "Is there a simpler version of this that would solve 80% of the problem?",
            "What would make you actively dislike this?",
        ],
    },
    "concept-walkthrough": {
        "opening": (
            "I'm going to walk you through a new workflow step by step. At each step, "
            "tell me what you'd actually do -- including if you'd skip it, get confused, "
            "or bail out."
        ),
        "core_questions": [
            "Step 1 is {topic}. What would you do here? Would you read this or skip past it?",
            "At this point you'd need to choose or configure something. What would you pick and why?",
            "What if an edge case happened here? Like you're interrupted, or the data is wrong, or you're on your phone?",
            "You've got realistic time constraints. Would you finish this flow or abandon it halfway?",
            "If something went wrong at step 3, what would you do? Call support? Give up? Try again later?",
            "How does this compare to how you'd do this today?",
        ],
        "anti_sycophancy_probes": [
            "Be honest -- at which step would most people in your role bail out?",
            "Is there a step here that feels like it was designed by someone who's never done your job?",
        ],
        "surprise_seekers": [],
    },
    "priority-ranking": {
        "opening": (
            "I'm going to give you several options. You can't say they're all important. "
            "I need you to pick, and tell me why."
        ),
        "core_questions": [
            "Here are the options: {topic}. If you could only have one, which one?",
            "Why that one? What happens in your week that makes it the priority?",
            "You just gave up the other options. What's the cost of not having those?",
            "Would your answer change if I asked this in a different season or context?",
            "You picked your top choice for yourself. Would your boss or colleague pick the same?",
            "For your top pick, what's the absolute minimum version that would still help?",
        ],
        "anti_sycophancy_probes": [
            "You ranked one option last. Is it actually useless, or just less urgent?",
            "If your top pick would take 6 months, would you still wait, or want a quick option first?",
        ],
        "surprise_seekers": [],
    },
}

SYNTHESIS_PROMPTS = [
    "What were the 3-5 strongest themes from this interview?",
    "What surprised me -- what did the persona say that I wouldn't have predicted from the profile alone?",
    "Where did the persona push back or express skepticism? What triggered it?",
    "What questions does this raise that should be tested with a real user?",
    "Where was I (the persona) speculating beyond my evidence base? Tag those as [speculative].",
]

INTERVIEW_RULES = """
=== INTERVIEW RULES ===
- Stay in character. Use the vocabulary and emotional tone from your profile.
- Ground your answers in your evidence base. Reference real pain points as your own experiences.
- If asked about something outside your evidence base, say "I don't really deal with that" or vary your answer.
- Push back when a proposed solution doesn't match your daily reality.
- When asked to prioritize, make hard tradeoffs. Never say "they're all important."
- If something sounds too good to be true, say so.
""".strip()
