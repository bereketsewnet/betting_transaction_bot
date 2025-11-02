"""Input validation utilities."""
import re
from typing import Optional, Tuple


def validate_callback_data(data: str, max_length: int = 64) -> Tuple[bool, Optional[str]]:
    """Validate callback data to prevent injection.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(data) > max_length:
        return False, f"Callback data too long (max {max_length} characters)"
    
    # Whitelist: alphanumeric, colon, underscore, hyphen
    if not re.match(r'^[a-z0-9:_-]+$', data.lower()):
        return False, "Invalid callback data format"
    
    return True, None


def validate_amount(amount_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """Validate amount input.
    
    Returns:
        tuple: (is_valid, amount_value, error_message)
    """
    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, None, "Amount must be greater than 0"
        if amount > 1000000:  # Max $1M
            return False, None, "Amount exceeds maximum limit"
        return True, amount, None
    except ValueError:
        return False, None, "Invalid amount format. Please enter a number."


def validate_player_site_id(site_id: str, max_length: int = 50) -> Tuple[bool, Optional[str]]:
    """Validate player site ID.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not site_id or not site_id.strip():
        return False, "Player site ID cannot be empty"
    
    if len(site_id) > max_length:
        return False, f"Player site ID too long (max {max_length} characters)"
    
    # Allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', site_id):
        return False, "Invalid player site ID format. Use only letters, numbers, underscore, and hyphen."
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number format.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Basic validation: starts with +, followed by digits
    pattern = r'^\+[1-9]\d{1,14}$'
    if not re.match(pattern, phone):
        return False, "Invalid phone format. Use format: +1234567890"
    return True, None


def mask_account_number(account_number: str, visible_digits: int = 4) -> str:
    """Mask account number for display.
    
    Example: "1234567890" -> "****7890"
    """
    if len(account_number) <= visible_digits:
        return "*" * len(account_number)
    
    masked = "*" * (len(account_number) - visible_digits)
    masked += account_number[-visible_digits:]
    return masked

