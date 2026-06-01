import re


def normalize_track(value: str) -> str:
    value = str(value).upper().strip()
    return re.sub(r"[^A-Z0-9]+", "", value)
