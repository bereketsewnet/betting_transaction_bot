"""Tests for validators."""
import pytest

from app.utils.validators import (
    validate_callback_data,
    validate_amount,
    validate_player_site_id,
    validate_email,
    mask_account_number,
)


def test_validate_callback_data():
    """Test callback data validation."""
    # Valid cases
    assert validate_callback_data("bank:deposit:1")[0] == True
    assert validate_callback_data("site:123")[0] == True
    
    # Invalid cases
    assert validate_callback_data("invalid callback!")[0] == False
    assert validate_callback_data("a" * 100)[0] == False  # Too long


def test_validate_amount():
    """Test amount validation."""
    # Valid cases
    is_valid, amount, error = validate_amount("100")
    assert is_valid == True
    assert amount == 100.0
    
    is_valid, amount, error = validate_amount("150.50")
    assert is_valid == True
    assert amount == 150.50
    
    # Invalid cases
    is_valid, amount, error = validate_amount("0")
    assert is_valid == False
    
    is_valid, amount, error = validate_amount("-10")
    assert is_valid == False
    
    is_valid, amount, error = validate_amount("invalid")
    assert is_valid == False


def test_validate_player_site_id():
    """Test player site ID validation."""
    # Valid cases
    assert validate_player_site_id("player123")[0] == True
    assert validate_player_site_id("player_123")[0] == True
    
    # Invalid cases
    assert validate_player_site_id("")[0] == False
    assert validate_player_site_id("a" * 100)[0] == False


def test_validate_email():
    """Test email validation."""
    # Valid cases
    assert validate_email("test@example.com")[0] == True
    
    # Invalid cases
    assert validate_email("invalid")[0] == False
    assert validate_email("invalid@")[0] == False


def test_mask_account_number():
    """Test account number masking."""
    assert mask_account_number("1234567890") == "****7890"
    assert mask_account_number("1234") == "****"
    assert mask_account_number("12345678") == "****5678"

