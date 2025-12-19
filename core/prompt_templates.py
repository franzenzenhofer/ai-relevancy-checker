"""Prompt templates for different languages - NATURAL, UNBIASED user prompts."""

# Natural German prompts - how real users actually ask
GERMAN_TEMPLATES = [
    "{query}?",                           # Direct question
    "Was genau ist {query}?",             # What exactly is
    "Gibt es {query}?",                   # Is there / Are there
    "Brauche Hilfe mit {query}",          # Need help with
    "Erkläre mir {query}",                # Explain to me
    "{query} - was muss ich wissen?",     # What do I need to know
    "Wie geht das mit {query}?",          # How does that work with
    "Infos zu {query} bitte",             # Info about please
]

# Natural English prompts - how real users actually ask
ENGLISH_TEMPLATES = [
    "{query}?",                           # Direct question
    "What exactly is {query}?",           # What exactly
    "Tell me about {query}",              # Tell me about
    "Need help with {query}",             # Need help
    "Explain {query}",                    # Explain
    "{query} - what should I know?",      # What should I know
    "How does {query} work?",             # How does it work
]


def generate_german_prompt(query: str) -> str:
    """Generate natural German hypothetical prompt."""
    query = query.strip()
    if "?" in query:
        return query
    if query.lower().startswith(("wie", "was", "wo", "wann", "wer", "welche")):
        return f"{query}?"
    template = GERMAN_TEMPLATES[hash(query) % len(GERMAN_TEMPLATES)]
    return template.format(query=query)


def generate_english_prompt(query: str) -> str:
    """Generate natural English hypothetical prompt."""
    query = query.strip()
    if "?" in query:
        return query
    if query.lower().startswith(("how", "what", "where", "when", "who", "which")):
        return f"{query}?"
    template = ENGLISH_TEMPLATES[hash(query) % len(ENGLISH_TEMPLATES)]
    return template.format(query=query)
