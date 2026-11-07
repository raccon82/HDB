import pytest
from unittest.mock import MagicMock
from src.masking import mask_nric
from src.validation import validate_nric, validate_unit_number, normalize_unit_number, validate_name
from src.database import add_record, check_unit_exists, get_all_records, search_records, export_records_to_excel, delete_all_records

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

def test_add_record_with_block_number():
    mock_supabase = MagicMock()
    # Mock check_unit_exists to return False
    mock_supabase.table().select().eq().execute.return_value.data = []
    
    # Mock insert response
    mock_inserted = [{"id": "123", "name": "John Tan", "unit_number": "#12-345", "block_number": "456"}]
    mock_supabase.table().insert().execute.return_value.data = mock_inserted
    
    # Mock get_all_records
    mock_supabase.table().select().order().execute.return_value.data = mock_inserted
    
    success, msg, details = add_record(mock_supabase, "John Tan", "123A", "#12-345", "456")
    assert success is True
    assert details["name"] == "John Tan"
    assert details["nric_masked"] == "123A"
    assert details["unit_number"] == "#12-345"
    assert details["block_number"] == "456"
    assert details["ticket_no"] == 1

def test_delete_all_records():
    mock_supabase = MagicMock()
    mock_supabase.table().delete().not_.is_().execute.return_value = MagicMock(data=[])
    
    success, msg = delete_all_records(mock_supabase)
    assert success is True
    assert "deleted successfully" in msg

