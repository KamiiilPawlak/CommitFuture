import regex as re

_POLISH_DIACRITICS_TRANSLATION = str.maketrans(
    {
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ź": "z",
        "ż": "z",
    }
)


def slugify(name: str) -> str:
    """Zamienia nazwę (technologii, soft skilla, domeny...) na slug do
    porównywania zbiorów między profilem kandydata a ogłoszeniem. '+' i '#'
    są zamieniane na słowa, nie usuwane - inaczej 'C', 'C++' i 'C#' spadłyby
    do tego samego sluga 'c'. Polskie znaki diakrytyczne są transliterowane
    (ć->c, ż->z...), nie usuwane - samo wyrzucenie ich regexem potrafi
    zlepić różne słowa w ten sam slug (np. 'Komunikatywność' gubiło
    końcówkę '-ść')."""
    slug = name.strip().lower()
    slug = slug.translate(_POLISH_DIACRITICS_TRANSLATION)
    slug = slug.replace("+", "p").replace("#", "sharp")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")
