"""In-memory storage implementation (ephemeral, for development only)."""
from typing import Optional, Any, Dict
from app.storage import StorageInterface
from app.logger import logger


class MemoryStorage(StorageInterface):
    """In-memory ephemeral storage (data lost on restart)."""
    
    def __init__(self):
        self._players: Dict[int, Dict[str, Any]] = {}
        self._state_data: Dict[int, Dict[str, Any]] = {}
        logger.warning("Using memory storage - data will be lost on restart!")
    
    async def get_player_uuid(self, telegram_id: int) -> Optional[str]:
        """Get player UUID for a telegram ID."""
        player = self._players.get(telegram_id)
        return player.get("player_uuid") if player else None
    
    async def set_player_uuid(self, telegram_id: int, player_uuid: str) -> None:
        """Store player UUID for a telegram ID."""
        if telegram_id not in self._players:
            self._players[telegram_id] = {}
        self._players[telegram_id]["player_uuid"] = player_uuid
    
    async def get_language(self, telegram_id: int) -> Optional[str]:
        """Get language code for a telegram ID."""
        player = self._players.get(telegram_id)
        return player.get("language_code") if player else None
    
    async def set_language(self, telegram_id: int, language_code: str) -> None:
        """Store language code for a telegram ID."""
        if telegram_id not in self._players:
            self._players[telegram_id] = {}
        self._players[telegram_id]["language_code"] = language_code
    
    async def get_state_data(self, telegram_id: int, key: str) -> Optional[Any]:
        """Get FSM state data."""
        user_state = self._state_data.get(telegram_id)
        return user_state.get(key) if user_state else None
    
    async def set_state_data(self, telegram_id: int, key: str, value: Any) -> None:
        """Set FSM state data."""
        if telegram_id not in self._state_data:
            self._state_data[telegram_id] = {}
        self._state_data[telegram_id][key] = value
    
    async def delete_state_data(self, telegram_id: int, key: str) -> None:
        """Delete FSM state data."""
        user_state = self._state_data.get(telegram_id)
        if user_state:
            user_state.pop(key, None)
    
    async def clear_state(self, telegram_id: int) -> None:
        """Clear all state data for a user."""
        self._state_data.pop(telegram_id, None)
    
    async def close(self) -> None:
        """Close storage connection."""
        self._players.clear()
        self._state_data.clear()
        logger.info("Memory storage cleared")

