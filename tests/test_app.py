import pytest
from src.masking import mask_nric
from src.validation import validate_nric, validate_unit_number, normalize_unit_number, validate_name

def test_mask_nric():
    assert mask_nric("123A") == "123A"
    assert mask_nric("765B") == "765B"
    assert mask_nric("") == ""

def test_validate_nric():
    assert validate_nric("123A") is True
    assert validate_nric("999Z") is True
    assert validate_nric("S1234567A") is False
    assert validate_nric("1234A") is False
    assert validate_nric("") is False

def test_validate_unit_number():
    assert validate_unit_number("#12-345") is True
    assert validate_unit_number("12-345") is True
    assert validate_unit_number("#01-1A") is True
    assert validate_unit_number("INVALID") is False
    assert validate_unit_number("") is False

def test_normalize_unit_number():
    assert normalize_unit_number(" #12-345 ") == "#12-345"
    assert normalize_unit_number("12-345") == "#12-345"
    assert normalize_unit_number("#01-1a") == "#01-1A"

def test_validate_name():
    assert validate_name("John Tan") is True
    assert validate_name("  ") is False
    assert validate_name("") is False
