import unicodedata
from typing import Final, cast

import ftfy
import regex

MOJIBAKE_MID_PATTERN: Final[regex.Pattern[str]] = regex.compile(
    r"(\p{L})[^\p{L}\s'`\-\.@+#/&+&](\p{L})"
)
MOJIBAKE_START_PATTERN: Final[regex.Pattern[str]] = regex.compile(
    r"\b[^\p{L}\s'`\-\.@+#/&+&](\p{L})"
)

GRAPHIC_NOISE_PATTERN: Final[regex.Pattern[str]] = regex.compile(
    r"[-_.*•■♦'`„”\"«»]{3,}"
)
CID_PATTERN: Final[regex.Pattern[str]] = regex.compile(r"\(cid:\d+\)")
BULLET_PATTERN: Final[regex.Pattern[str]] = regex.compile(r"[■♦•:-]")

WHITESPACE_INLINE_PATTERN: Final[regex.Pattern[str]] = regex.compile(r"[\p{Zs}\t]+")
MULTILINE_REDUNDANT_NEWLINES: Final[regex.Pattern[str]] = regex.compile(r"\n{3,}")


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _repair_ocr_mojibake(text: str) -> str:
    text = ftfy.fix_text(text)

    text: str = MOJIBAKE_MID_PATTERN.sub(r"\1ż\2", text)
    return cast(str, MOJIBAKE_START_PATTERN.sub(r"ż\1", text))


def _remove_graphic_noise(text: str) -> str:
    text: str = GRAPHIC_NOISE_PATTERN.sub(" ", text)
    text: str = CID_PATTERN.sub(" ", text)
    return cast(str, BULLET_PATTERN.sub(" ", text))


def _normalize_whitespace(text: str) -> str:
    text: str = WHITESPACE_INLINE_PATTERN.sub(" ", text)
    text: str = "\n".join(line.strip() for line in text.splitlines())
    return cast(str, MULTILINE_REDUNDANT_NEWLINES.sub("\n\n", text))


def clean_ocr_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text: str = _normalize_unicode(raw_text)
    text: str = _repair_ocr_mojibake(text)
    text: str = _remove_graphic_noise(text)
    text: str = _normalize_whitespace(text)

    return text.strip()
