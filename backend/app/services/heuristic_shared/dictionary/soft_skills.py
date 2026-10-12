from .lookup_engine import FlashLookupEngine

# Frazy-klucze opisujące kompetencje miękkie, typowe dla ogłoszeń o pracę.
# Kanoniczny tag jest już slugiem (żeby nie trzeba było dodatkowo slugować
# przy matchingu) - patrz slug.py dla tej samej konwencji po stronie
# kandydata.
SOFT_SKILLS_DICTIONARY: dict[str, list[str]] = {
    "ownership": [
        "ownership mindset",
        "take ownership",
        "ownership",
        "poczucie odpowiedzialności",
    ],
    "communication": [
        "communication skills",
        "excellent communication",
        "communication",
        "umiejętności komunikacyjne",
        "komunikatywność",
    ],
    "independent_work": [
        "work independently",
        "ability to work independently",
        "independent work",
        "samodzielność",
        "praca samodzielna",
    ],
    "problem_solving": [
        "problem-solving",
        "problem solving",
        "strong problem-solving skills",
        "umiejętności analityczne",
        "rozwiązywanie problemów",
    ],
    "cross_functional_collaboration": [
        "cross-functional teams",
        "cross-functional collaboration",
        "distributed teams",
        "praca w zespołach rozproszonych",
        "współpraca międzyzespołowa",
    ],
    "mentoring": [
        "mentoring",
        "mentorship",
        "mentoring młodszych",
    ],
    "team_leadership": [
        "team leadership",
        "leading a team",
        "zarządzanie zespołem",
        "kierowanie zespołem",
    ],
    "attention_to_detail": [
        "attention to detail",
        "dokładność",
        "skrupulatność",
    ],
    "adaptability": [
        "adaptability",
        "fast-paced environment",
        "elastyczność",
    ],
    "teamwork": [
        "teamwork",
        "team player",
        "praca w zespole",
        "praca zespołowa",
    ],
}

_soft_skills_engine = FlashLookupEngine(SOFT_SKILLS_DICTIONARY)


def extract_soft_skill_tags(text: str) -> list[str]:
    return _soft_skills_engine.extract_matches(text)
