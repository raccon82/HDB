"""
Validation and normalization module for NRIC and Unit Numbers.
"""
import re

def validate_nric(nric: str) -> bool:
    """
    Validates partial NRIC/FIN format (last 3 digits and an alphabet, e.g., 123A).
    """
    if not nric:
        return False
    cleaned = nric.strip().upper()
    pattern = r"^\d{3}[A-Z]$"
    return bool(re.match(pattern, cleaned))

def validate_unit_number(unit_number: str) -> bool:
    """
    Validates reasonable HDB/residential unit number format.
    Typically looks like #12-345, 12-345, #01-1A, etc.
    We check for presence of digits separated by a hyphen.
    """
    if not unit_number:
        return False
    cleaned = unit_number.strip()
    # Pattern allowing optional '#' prefix, block/floor numbers, and hyphen
    pattern = r"^#?\d+-\d+[A-Za-z]?$"
    return bool(re.match(pattern, cleaned))

def normalize_unit_number(unit_number: str) -> str:
    """
    Normalizes unit number to prevent formatting differences from creating duplicate records.
    Example: 
    ' #12-345 ' -> '#12-345'
    '12-345' -> '#12-345'
    '#12-345 ' -> '#12-345'
    Converts to uppercase and ensures a leading '#' for consistency.
    """
    if not unit_number:
        return ""
    cleaned = unit_number.strip().upper()
    if not cleaned.startswith("#"):
        cleaned = "#" + cleaned
    return cleaned

def validate_name(name: str) -> bool:
    """
    Validates that name is not empty and has valid characters.
    """
    if not name:
        return False
    return len(name.strip()) > 0
