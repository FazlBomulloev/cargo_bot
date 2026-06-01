import re


def validate_phone(text: str) -> str | None:
    cleaned = re.sub(r"[\s\-\(\)]+", "", (text or "").strip())
    cleaned = cleaned.lstrip("+")
    if re.fullmatch(r"992\d{9}", cleaned):
        return f"+{cleaned}"
    if re.fullmatch(r"\d{9}", cleaned):
        return f"+992{cleaned}"
    return None
