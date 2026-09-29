import phonenumbers
from phonenumbers import PhoneNumberFormat, PhoneNumberMatcher


def extract_phones(text: str | None, default_region: str = "PL") -> list[str]:
    if not text or not text.strip():
        return []

    extracted_phones = {
        phonenumbers.format_number(match.number, PhoneNumberFormat.E164)
        for match in PhoneNumberMatcher(text, default_region)
        if phonenumbers.is_valid_number(match.number)
    }

    return list(extracted_phones)
