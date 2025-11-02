"""Notify service for handling backend notifications."""
from typing import Optional, Dict, Any
import logging
from aiogram import Bot
from app.storage import StorageInterface
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)


class NotifyService:
    """Service for handling backend notifications."""
    
    def __init__(self, bot: Bot, storage: StorageInterface, api_client: APIClient):
        self.bot = bot
        self.storage = storage
        self.api_client = api_client
    
    async def send_notification(
        self,
        player_uuid: str,
        message: str,
        transaction_uuid: Optional[str] = None,
    ) -> bool:
        """Send notification to player by player UUID."""
        try:
            # Get telegram_id from player_uuid
            # Note: This requires reverse lookup - we store telegram_id -> player_uuid
            # TODO: Consider adding player_uuid -> telegram_id mapping for better lookup
            telegram_id = await self._find_telegram_id_by_player_uuid(player_uuid)
            
            if not telegram_id:
                logger.warning(f"Could not find telegram_id for player_uuid {player_uuid}")
                return False
            
            await self.bot.send_message(chat_id=telegram_id, text=message)
            logger.info(f"Sent notification to telegram_id {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def _find_telegram_id_by_player_uuid(self, player_uuid: str) -> Optional[int]:
        """Find telegram_id by player_uuid (reverse lookup)."""
        # TODO: Implement efficient reverse lookup
        # For now, we'd need to query all players or maintain reverse mapping
        # This is a limitation of the current storage design
        # In production, consider adding player_uuid -> telegram_id index
        logger.warning("Reverse lookup not fully implemented - consider adding reverse mapping")
        return None
    
    async def handle_backend_notification(self, notification_data: Dict[str, Any]) -> None:
        """Handle notification from backend webhook."""
        player_uuid = notification_data.get("playerUuid")
        transaction_uuid = notification_data.get("transactionUuid")
        status = notification_data.get("status")
        message = notification_data.get("message", "")
        
        if not player_uuid:
            logger.error("Notification missing playerUuid")
            return
        
        # Format notification message
        if not message:
            message = f"Transaction {transaction_uuid} status updated to {status}"
        
        await self.send_notification(player_uuid, message, transaction_uuid)

