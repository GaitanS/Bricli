"""
Search filter utilities for handling counties, queries, and validation
"""

import unicodedata

from django.utils.text import slugify

from accounts.models import County


def normalize_slug(text):
    """
    Normalize text to slug format with Romanian transliteration
    ț/Ț → t, ș/Ș → s, ă/Ă → a, â/Â/î/Î → i/a

    Args:
        text: String to normalize

    Returns:
        ASCII-only slug string
    """
    if not text:
        return ""

    # Romanian-specific replacements
    replacements = {
        "ț": "t",
        "Ț": "t",
        "ș": "s",
        "Ș": "s",
        "ă": "a",
        "Ă": "a",
        "â": "a",
        "Â": "a",
        "î": "i",
        "Î": "i",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove other diacritics and create slug
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    return slugify(text)


def sanitize_query(query):
    """
    Sanitize search query by stripping whitespace and collapsing multiple spaces
    Returns empty string if query is too short (< 2 chars)

    Args:
        query: Search query string

    Returns:
        Sanitized query string or empty string
    """
    if not query:
        return ""

    # Strip and collapse multiple spaces
    sanitized = " ".join(query.strip().split())

    # Return empty if too short
    if len(sanitized) < 2:
        return ""

    return sanitized


def get_county_by_any(value):
    """
    Get County object by id, slug, or name
    Returns None for invalid values like '.', 'all', empty strings, etc.

    Args:
        value: County identifier (id, slug, or name)

    Returns:
        County object or None
    """
    if not value:
        return None

    # Ignore placeholder/invalid values
    if value.lower() in [".", "all", "toate", "none", "null"]:
        return None

    # Try by ID first (numeric)
    if value.isdigit():
        try:
            return County.objects.get(pk=int(value))
        except (County.DoesNotExist, ValueError):
            return None

    # Try by slug (normalized)
    normalized = normalize_slug(value)
    if normalized:
        try:
            return County.objects.get(slug=normalized)
        except County.DoesNotExist:
            pass

    # Try by exact name match
    try:
        return County.objects.get(name__iexact=value)
    except County.DoesNotExist:
        return None
