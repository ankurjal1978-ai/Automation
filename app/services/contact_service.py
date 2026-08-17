import re
from typing import Dict, List, Set

from app.config import REQUIRED_FIELDS


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_contact_row(row: Dict[str, str]) -> Dict[str, str]:
    cleaned = {}
    for key, value in row.items():
        if value is None:
            cleaned[key] = ""
        else:
            cleaned[key] = str(value).strip()

    cleaned["email"] = cleaned.get("email", "").strip().lower()
    for field in ["first_name", "last_name", "company", "title", "website", "industry", "country", "campaign"]:
        cleaned[field] = cleaned.get(field, "").strip()

    return cleaned


def validate_contact(row: Dict[str, str]) -> List[str]:
    cleaned = normalize_contact_row(row)
    errors: List[str] = []

    for field in REQUIRED_FIELDS:
        if not cleaned.get(field, "").strip():
            errors.append(f"{field} is required")

    email = cleaned.get("email", "")
    if email and not EMAIL_REGEX.match(email):
        errors.append("email is invalid")

    return errors


def detect_duplicate_emails(rows: List[Dict[str, str]]) -> Set[str]:
    seen = set()
    duplicates = set()

    for row in rows:
        email = normalize_contact_row(row).get("email", "")
        if not email:
            continue
        if email in seen:
            duplicates.add(email)
        else:
            seen.add(email)

    return duplicates
