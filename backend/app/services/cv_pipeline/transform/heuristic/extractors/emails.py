import regex

EMAIL_PATTERN: regex.Pattern[str] = regex.compile(
    r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}", regex.IGNORECASE
)


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    if not match:
        return None

    return str(match.group(0)).strip().lower()
