from .lookup_engine import FlashLookupEngine

# Tagi domenowe/branżowe (głównie pod "nice to have" w ogłoszeniach, ale
# szukane w całym tekście - sygnał domenowy często pada też we wstępie
# ogłoszenia, nie tylko w wydzielonej sekcji). To jest skromny, startowy
# zestaw - rozszerzać wg realnych ogłoszeń, które trzeba będzie matchować.
DOMAIN_DICTIONARY: dict[str, list[str]] = {
    "data_analytics": [
        "data analytics",
        "data analysis",
        "analiza danych",
        "business intelligence",
    ],
    "scientific_research": [
        "scientific software",
        "scientific workflows",
        "research-oriented",
        "oprogramowanie naukowe",
        "badania naukowe",
    ],
    "pharma_lifesciences": [
        "pharmaceutical",
        "pharma",
        "life sciences",
        "laboratory systems",
        "chromatography",
        "farmaceutyczny",
        "przemysł farmaceutyczny",
    ],
    "regulated_compliance": [
        "gxp",
        "regulated environment",
        "regulatory compliance",
        "środowisko regulowane",
        "zgodność regulacyjna",
    ],
    "fintech": [
        "fintech",
        "financial services",
        "banking",
        "payments",
        "sektor finansowy",
        "bankowość",
    ],
    "healthcare": [
        "healthcare",
        "medtech",
        "ochrona zdrowia",
        "medycyna",
    ],
    "ecommerce": [
        "e-commerce",
        "ecommerce",
        "online retail",
        "handel elektroniczny",
    ],
    "gaming": [
        "gamedev",
        "game development",
        "gaming industry",
        "branża gier",
    ],
    "automotive": [
        "automotive",
        "motoryzacja",
    ],
    "telecom": [
        "telecom",
        "telecommunications",
        "telekomunikacja",
    ],
    "cybersecurity": [
        "cybersecurity",
        "information security",
        "cyberbezpieczeństwo",
    ],
    "public_sector": [
        "public sector",
        "government",
        "sektor publiczny",
        "administracja publiczna",
    ],
    "logistics_supply_chain": [
        "logistics",
        "supply chain",
        "logistyka",
        "łańcuch dostaw",
    ],
    "manufacturing": [
        "manufacturing",
        "przemysł produkcyjny",
        "produkcja przemysłowa",
    ],
    "legaltech": [
        "legaltech",
        "legal tech",
    ],
    "edtech": [
        "edtech",
        "e-learning",
    ],
}

_domains_engine = FlashLookupEngine(DOMAIN_DICTIONARY)


def extract_domain_tags(text: str) -> list[str]:
    return _domains_engine.extract_matches(text)
