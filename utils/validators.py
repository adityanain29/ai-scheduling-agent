# utils/validators.py
# Minimal validation helpers used across the app.

import re
from datetime import datetime
from typing import Optional

EMAIL_FULL_REGEX = re.compile(
    r"^(?=.{1,254}$)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

def is_valid_email(value: Optional[str]) -> bool:
    if not value:
        return False
    v = value.strip()
    return EMAIL_FULL_REGEX.match(v) is not None

def is_valid_date_yyyy_mm_dd(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except Exception:
        return False

def is_valid_full_name(value: Optional[str]) -> bool:
    if not value:
        return False
    parts = [p for p in value.strip().split() if p]
    if len(parts) < 2:
        return False
    # Ensure most characters are alphabetic; allow hyphens and apostrophes
    letters = re.sub(r"[^A-Za-z\-'\s]", "", value)
    return len(letters.replace(" ", "")) >= max(3, int(0.8 * len(value.replace(" ", ""))))