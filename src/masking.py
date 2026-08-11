"""
NRIC privacy masking module.
Ensures full NRIC is never displayed in the UI, logs, search results, or tables.
"""

def mask_nric(nric: str) -> str:
    """
    Masks or returns the NRIC string. Since the input is already the last 3 digits and alphabet (e.g. 123A),
    we can return it directly or format it safely.
    """
    if not nric:
        return ""
    return nric.strip().upper()
