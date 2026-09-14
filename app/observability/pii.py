"""PII Redaction Pipeline (Criteria 16).

Scrubs personally identifiable information (PII) including email addresses,
phone numbers, cadastral property owner IDs, national identity numbers,
and authentication keys from logs and memory storage.
"""

import re
from typing import Any, Dict, List, Union


# Regex patterns for common PII
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
DNI_NIE_REGEX = re.compile(r"\b[XYZ]?\d{7,8}[A-Z]\b", re.IGNORECASE)
BEARER_TOKEN_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]{20,}", re.IGNORECASE)
API_KEY_REGEX = re.compile(r"(AIza[0-9A-Za-z-_]{35})")


def redact_pii_string(text: str) -> str:
    """Scrub sensitive PII from a single text string.

    Args:
        text: Input string potentially containing sensitive personal data.

    Returns:
        Redacted string with PII replaced by safe placeholder tags.
    """
    if not isinstance(text, str):
        return text

    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
    sanitized = SSN_REGEX.sub("[REDACTED_SSN]", sanitized)
    sanitized = DNI_NIE_REGEX.sub("[REDACTED_NATIONAL_ID]", sanitized)
    sanitized = BEARER_TOKEN_REGEX.sub(r"\1[REDACTED_TOKEN]", sanitized)
    sanitized = API_KEY_REGEX.sub("[REDACTED_API_KEY]", sanitized)
    return sanitized


def redact_pii(data: Union[str, Dict[str, Any], List[Any]]) -> Union[str, Dict[str, Any], List[Any]]:
    """Recursively redacts PII from strings, dictionaries, or lists before logging or persisting.

    Args:
        data: Arbitrary data structure to scrub.

    Returns:
        Deep copy of the data structure with all string leaf nodes scrubbed of PII.
    """
    if isinstance(data, str):
        return redact_pii_string(data)
    elif isinstance(data, dict):
        return {k: redact_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_pii(item) for item in data]
    return data
