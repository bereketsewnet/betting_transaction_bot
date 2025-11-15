"""Text templates for bot messages."""
from typing import Optional, Dict, Any
from app.services.api_client import APIClient
from app.storage import StorageInterface
import logging

logger = logging.getLogger(__name__)


class TextTemplates:
    """Text template manager."""
    
    def __init__(self, api_client: APIClient, storage: Optional[StorageInterface] = None):
        self.api_client = api_client
        self.storage = storage
    
    async def get_template(self, key: str, language_code: str = "en", default: str = "") -> str:
        """
        Get template by key and language code.
        Falls back to English if template not found for requested language.
        Falls back to default string if English template also not found.
        
        Args:
            key: Template key name
            language_code: Language code (e.g., 'en', 'am')
            default: Default text to return if template not found
        
        Returns:
            Template content or default string
        """
        try:
            response = await self.api_client.get_template(key, language_code)
            content = response.get("content", "")
            # Return content if available, otherwise return default
            return content.strip() if content else default
        except Exception as e:
            logger.warning(f"Failed to get template '{key}' for language '{language_code}': {e}")
            # If requested language is not English, try English fallback
            if language_code != "en":
                try:
                    response = await self.api_client.get_template(key, "en")
                    content = response.get("content", "")
                    if content:
                        logger.info(f"Using English fallback for template '{key}'")
                        return content.strip()
                except Exception:
                    pass
            # Return default if all else fails
            return default
    
    async def get_welcome_message(self, language_code: str = "en") -> str:
        """Get welcome message from API."""
        return await self.get_template("welcome_message", language_code, "")
    
    async def get_user_language(self, telegram_id: int) -> str:
        """Get user's language code from storage, default to 'en'."""
        if self.storage:
            lang = await self.storage.get_language(telegram_id)
            return lang if lang else "en"
        return "en"
    
    @staticmethod
    def format_transaction_details(transaction: dict) -> str:
        """Format transaction details for display."""
        lines = [
            f"📋 Transaction Details",
            f"",
            f"ID: {transaction.get('transactionUuid', 'N/A')}",
            f"Type: {transaction.get('type', 'N/A')}",
            f"Amount: {transaction.get('currency', 'USD')} {transaction.get('amount', '0')}",
            f"Status: {transaction.get('status', 'N/A')}",
        ]
        
        if transaction.get('depositBank'):
            bank = transaction['depositBank']
            lines.append(f"Bank: {bank.get('bankName', 'N/A')}")
        
        if transaction.get('withdrawalBank'):
            bank = transaction['withdrawalBank']
            lines.append(f"Bank: {bank.get('bankName', 'N/A')}")
        
        if transaction.get('bettingSite'):
            site = transaction['bettingSite']
            lines.append(f"Betting Site: {site.get('name', 'N/A')}")
        
        if transaction.get('screenshotUrl'):
            lines.append(f"Screenshot: {transaction['screenshotUrl']}")
        
        if transaction.get('requestedAt'):
            lines.append(f"Requested: {transaction['requestedAt']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_bank_details(bank: dict) -> str:
        """Format bank details for display."""
        lines = [
            "Bank Details:",
            f"Bank: {bank.get('bankName', 'N/A')}",
            f"Account Name: {bank.get('accountName', 'N/A')}",
            f"Account Number: {bank.get('accountNumber', 'N/A')}",
        ]
        
        if bank.get('notes'):
            lines.append(f"Notes: {bank.get('notes', 'N/A')}")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_error_message(error: str) -> str:
        """Get user-friendly error message."""
        error_messages = {
            "Player not found": "❌ Player profile not found. Please try again.",
            "Transaction not found": "❌ Transaction not found.",
            "Validation failed": "❌ Invalid input. Please check your data and try again.",
            "File too large": "❌ File is too large. Maximum size is 5MB.",
            "Invalid file type": "❌ Invalid file type. Only PNG, JPG, and JPEG are allowed.",
        }
        return error_messages.get(error, f"❌ Error: {error}")

