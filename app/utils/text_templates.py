"""Text templates for bot messages."""
from typing import Optional
from app.services.api_client import APIClient


class TextTemplates:
    """Text template manager."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def get_welcome_message(self, language_code: str = "en") -> str:
        """Get welcome message from API."""
        try:
            response = await self.api_client.get_welcome(language_code)
            return response.message
        except Exception:
            # Fallback message
            return "Welcome to Betting Payment Manager! Please choose your preferred language to continue."
    
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
            f"🏦 {bank.get('bankName', 'Bank')}",
            f"Account: {bank.get('accountName', 'N/A')}",
        ]
        
        if bank.get('accountNumber'):
            from app.utils.validators import mask_account_number
            masked = mask_account_number(bank['accountNumber'])
            lines.append(f"Account Number: {masked}")
        
        if bank.get('notes'):
            lines.append(f"Notes: {bank['notes']}")
        
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

