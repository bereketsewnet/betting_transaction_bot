"""In-memory storage implementation (ephemeral, for development only)."""
from typing import Optional, Any, Dict
from app.storage import StorageInterface
from app.logger import logger


class MemoryStorage(StorageInterface):
    """In-memory ephemeral storage (data lost on restart)."""
    
    def __init__(self):
        self._players: Dict[int, Dict[str, Any]] = {}
        self._state_data: Dict[int, Dict[str, Any]] = {}
        self._credentials: Dict[int, Dict[str, str]] = {}
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
    
    async def set_user_credentials(self, telegram_id: int, email: str, password: str) -> None:
        """Store user credentials locally."""
        self._credentials[telegram_id] = {"email": email, "password": password}
        logger.info(f"💾 Stored credentials for telegram_id {telegram_id}")
    
    async def get_user_credentials(self, telegram_id: int) -> Optional[Dict[str, str]]:
        """Get stored user credentials."""
        return self._credentials.get(telegram_id)
    
    async def is_user_logged_in(self, telegram_id: int) -> bool:
        """Check if user has stored credentials (is logged in)."""
        return telegram_id in self._credentials
    
    async def clear_user_credentials(self, telegram_id: int) -> None:
        """Clear stored user credentials (logout)."""
        self._credentials.pop(telegram_id, None)
        logger.info(f"🗑️ Cleared credentials for telegram_id {telegram_id}")
    
    async def set_admin_token(self, telegram_id: int, access_token: str, role: str) -> None:
        """Store admin access token and role."""
        if telegram_id not in self._credentials:
            self._credentials[telegram_id] = {}
        self._credentials[telegram_id]["access_token"] = access_token
        self._credentials[telegram_id]["role"] = role
        logger.info(f"💾 Stored admin token for telegram_id {telegram_id}, role: {role}")
    
    async def get_admin_token(self, telegram_id: int) -> Optional[str]:
        """Get admin access token."""
        creds = self._credentials.get(telegram_id)
        return creds.get("access_token") if creds else None
    
    async def get_user_role(self, telegram_id: int) -> Optional[str]:
        """Get user role (admin, agent, player)."""
        creds = self._credentials.get(telegram_id)
        return creds.get("role") if creds else None
    
    async def clear_admin_token(self, telegram_id: int) -> None:
        """Clear admin access token (logout)."""
        if telegram_id in self._credentials:
            self._credentials[telegram_id].pop("access_token", None)
            self._credentials[telegram_id].pop("role", None)
        logger.info(f"🗑️ Cleared admin token for telegram_id {telegram_id}")
    
    async def close(self) -> None:
        """Close storage connection."""
        self._players.clear()
        self._state_data.clear()
        self._credentials.clear()
        logger.info("Memory storage cleared")

