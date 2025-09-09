# utils/helpers.py
# Lightweight helpers for parsing and normalization.

import re
from datetime import datetime
from typing import Optional

# RFC 5322-inspired, simplified for practical use
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def extract_email(text: str) -> Optional[str]:
    """
    Extract the first email-like token from free text.
    """
    if not text:
        return None
    match = EMAIL_REGEX.search(text)
    return match.group(0).strip() if match else None

def normalize_name(full_name: Optional[str]) -> Optional[str]:
    """
    Normalize spacing and capitalization for names.
    """
    if not full_name:
        return None
    return " ".join(full_name.split()).title()

def parse_date_to_yyyy_mm_dd(value: Optional[str]) -> Optional[str]:
    """
    Parse common date formats and return YYYY-MM-DD or None.
    """
    if not value:
        return None
    value = value.strip()
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",   # e.g., September 08, 2025
        "%b %d, %Y",   # e.g., Sep 08, 2025
        "%Y.%m.%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None