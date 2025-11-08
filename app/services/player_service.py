"""Player service for managing player profiles."""
from typing import Optional
from app.services.api_client import APIClient
from app.storage import StorageInterface
from app.schemas.api_models import PlayerResponse
import logging

logger = logging.getLogger(__name__)


class PlayerService:
    """Service for player operations."""
    
    def __init__(self, api_client: APIClient, storage: StorageInterface):
        self.api_client = api_client
        self.storage = storage
    
    async def get_or_create_guest_player(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        language_code: str = "en",
    ) -> str:
        """Get or create guest player UUID."""
        # Check if we already have a player UUID
        player_uuid = await self.storage.get_player_uuid(telegram_id)
        if player_uuid:
            return player_uuid
        
        # Create new guest player
        try:
            # Ensure telegram_username is a string (API requires string, not None)
            telegram_username_str = telegram_username if telegram_username else ""
            
            response: PlayerResponse = await self.api_client.create_player(
                telegram_id=str(telegram_id),
                telegram_username=telegram_username_str,
                language_code=language_code,
            )
            player_uuid = response.player.playerUuid
            await self.storage.set_player_uuid(telegram_id, player_uuid)
            await self.storage.set_language(telegram_id, language_code)
            logger.info(f"Created guest player {player_uuid} for telegram_id {telegram_id}")
            return player_uuid
        except Exception as e:
            logger.error(f"Failed to create guest player: {e}")
            raise
    
    async def register_player(
        self,
        telegram_id: int,
        telegram_username: Optional[str],
        language_code: str,
        username: str,
        email: str,
        password: str,
        display_name: str,
        phone: Optional[str] = None,
    ) -> str:
        """Register player with full account."""
        try:
            response: PlayerResponse = await self.api_client.register_player(
                telegram_id=str(telegram_id),
                telegram_username=telegram_username,
                language_code=language_code,
                username=email,  # Email is used as username
                email=email,
                password=password,
                display_name=display_name,
                phone=phone,
            )
            player_uuid = response.player.playerUuid
            await self.storage.set_player_uuid(telegram_id, player_uuid)
            await self.storage.set_language(telegram_id, language_code)
            
            # Store credentials locally so user doesn't need to login again
            await self.storage.set_user_credentials(telegram_id, email, password)
            
            logger.info(f"✅ Registered player {player_uuid} for telegram_id {telegram_id} and stored credentials")
            return player_uuid
        except Exception as e:
            logger.error(f"Failed to register player: {e}")
            raise
    
    async def get_player_uuid(self, telegram_id: int) -> Optional[str]:
        """Get player UUID from storage."""
        return await self.storage.get_player_uuid(telegram_id)
    
    async def get_language(self, telegram_id: int) -> Optional[str]:
        """Get player language from storage."""
        return await self.storage.get_language(telegram_id)
    
    async def set_language(self, telegram_id: int, language_code: str) -> None:
        """Set player language."""
        await self.storage.set_language(telegram_id, language_code)

