"""Storage abstraction for FSM and player mappings."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage.sqlite_storage import SQLiteStorage
    from app.storage.memory_storage import MemoryStorage

from app.config import config


class StorageInterface(ABC):
    """Storage interface for FSM and player data."""
    
    @abstractmethod
    async def get_player_uuid(self, telegram_id: int) -> Optional[str]:
        """Get player UUID for a telegram ID."""
        pass
    
    @abstractmethod
    async def set_player_uuid(self, telegram_id: int, player_uuid: str) -> None:
        """Store player UUID for a telegram ID."""
        pass
    
    @abstractmethod
    async def get_language(self, telegram_id: int) -> Optional[str]:
        """Get language code for a telegram ID."""
        pass
    
    @abstractmethod
    async def set_language(self, telegram_id: int, language_code: str) -> None:
        """Store language code for a telegram ID."""
        pass
    
    @abstractmethod
    async def get_state_data(self, telegram_id: int, key: str) -> Optional[Any]:
        """Get FSM state data."""
        pass
    
    @abstractmethod
    async def set_state_data(self, telegram_id: int, key: str, value: Any) -> None:
        """Set FSM state data."""
        pass
    
    @abstractmethod
    async def delete_state_data(self, telegram_id: int, key: str) -> None:
        """Delete FSM state data."""
        pass
    
    @abstractmethod
    async def clear_state(self, telegram_id: int) -> None:
        """Clear all state data for a user."""
        pass
    
    @abstractmethod
    async def set_user_credentials(self, telegram_id: int, email: str, password: str) -> None:
        """Store user credentials locally."""
        pass
    
    @abstractmethod
    async def get_user_credentials(self, telegram_id: int) -> Optional[Dict[str, str]]:
        """Get stored user credentials."""
        pass
    
    @abstractmethod
    async def is_user_logged_in(self, telegram_id: int) -> bool:
        """Check if user has stored credentials (is logged in)."""
        pass
    
    @abstractmethod
    async def clear_user_credentials(self, telegram_id: int) -> None:
        """Clear stored user credentials (logout)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close storage connection."""
        pass


def get_storage() -> StorageInterface:
    """Get storage instance based on configuration."""
    # Import here to avoid circular import
    from app.storage.sqlite_storage import SQLiteStorage
    from app.storage.memory_storage import MemoryStorage
    
    if config.STORAGE_MODE == "sqlite":
        return SQLiteStorage(config.DB_PATH)
    else:
        return MemoryStorage()

