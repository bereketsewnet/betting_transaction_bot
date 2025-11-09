"""SQLite storage implementation for persistent data."""
import aiosqlite
import json
from typing import Optional, Any, Dict
from pathlib import Path
from app.storage import StorageInterface
from app.logger import logger


class SQLiteStorage(StorageInterface):
    """SQLite-based persistent storage."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._connection is None:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._init_db()
        return self._connection
    
    async def _init_db(self) -> None:
        """Initialize database schema."""
        conn = await self._get_connection()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                telegram_id INTEGER PRIMARY KEY,
                player_uuid TEXT NOT NULL,
                language_code TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS state_data (
                telegram_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (telegram_id, key),
                FOREIGN KEY (telegram_id) REFERENCES players(telegram_id) ON DELETE CASCADE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                telegram_id INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES players(telegram_id) ON DELETE CASCADE
            )
        """)
        
        # Add new columns if they don't exist (migration for existing databases)
        try:
            await conn.execute("ALTER TABLE user_credentials ADD COLUMN access_token TEXT")
            logger.info("✅ Added access_token column to user_credentials table")
        except Exception as e:
            # Column might already exist, or table might not exist yet
            if "duplicate column" not in str(e).lower() and "no such table" not in str(e).lower():
                logger.debug(f"Could not add access_token column: {e}")
        
        try:
            await conn.execute("ALTER TABLE user_credentials ADD COLUMN role TEXT")
            logger.info("✅ Added role column to user_credentials table")
        except Exception as e:
            # Column might already exist
            if "duplicate column" not in str(e).lower() and "no such table" not in str(e).lower():
                logger.debug(f"Could not add role column: {e}")
        
        await conn.commit()
        logger.info("SQLite database initialized")
    
    async def get_player_uuid(self, telegram_id: int) -> Optional[str]:
        """Get player UUID for a telegram ID."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT player_uuid FROM players WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["player_uuid"] if row else None
    
    async def set_player_uuid(self, telegram_id: int, player_uuid: str) -> None:
        """Store player UUID for a telegram ID."""
        conn = await self._get_connection()
        await conn.execute(
            """INSERT OR REPLACE INTO players (telegram_id, player_uuid, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (telegram_id, player_uuid)
        )
        await conn.commit()
    
    async def get_language(self, telegram_id: int) -> Optional[str]:
        """Get language code for a telegram ID."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT language_code FROM players WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["language_code"] if row else None
    
    async def set_language(self, telegram_id: int, language_code: str) -> None:
        """Store language code for a telegram ID."""
        conn = await self._get_connection()
        
        # Check if player exists
        async with conn.execute(
            "SELECT player_uuid FROM players WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if row:
            # Player exists, update language
            await conn.execute(
                """UPDATE players 
                   SET language_code = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE telegram_id = ?""",
                (language_code, telegram_id)
            )
        else:
            # Player doesn't exist, need to create one first with a placeholder UUID
            # This should not happen normally, but handle it gracefully
            from uuid import uuid4
            placeholder_uuid = str(uuid4())
            await conn.execute(
                """INSERT INTO players (telegram_id, player_uuid, language_code, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (telegram_id, placeholder_uuid, language_code)
            )
        await conn.commit()
    
    async def get_state_data(self, telegram_id: int, key: str) -> Optional[Any]:
        """Get FSM state data."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT value FROM state_data WHERE telegram_id = ? AND key = ?",
            (telegram_id, key)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["value"]:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]
            return None
    
    async def set_state_data(self, telegram_id: int, key: str, value: Any) -> None:
        """Set FSM state data."""
        conn = await self._get_connection()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        await conn.execute(
            """INSERT OR REPLACE INTO state_data (telegram_id, key, value)
               VALUES (?, ?, ?)""",
            (telegram_id, key, value_str)
        )
        await conn.commit()
    
    async def delete_state_data(self, telegram_id: int, key: str) -> None:
        """Delete FSM state data."""
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM state_data WHERE telegram_id = ? AND key = ?",
            (telegram_id, key)
        )
        await conn.commit()
    
    async def clear_state(self, telegram_id: int) -> None:
        """Clear all state data for a user."""
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM state_data WHERE telegram_id = ?",
            (telegram_id,)
        )
        await conn.commit()
    
    async def set_user_credentials(self, telegram_id: int, email: str, password: str) -> None:
        """Store user credentials locally (encrypted for security)."""
        conn = await self._get_connection()
        # For simplicity, store password as-is (in production, use encryption)
        # TODO: Add encryption for password storage
        
        # Check if record exists to preserve access_token and role
        async with conn.execute(
            "SELECT access_token, role FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
        
        if row:
            # Update existing record, preserving access_token and role
            await conn.execute(
                """UPDATE user_credentials 
                   SET email = ?, password = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE telegram_id = ?""",
                (email, password, telegram_id)
            )
        else:
            # Insert new record
            await conn.execute(
                """INSERT INTO user_credentials 
                   (telegram_id, email, password, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (telegram_id, email, password)
            )
        await conn.commit()
        logger.info(f"💾 Stored credentials for telegram_id {telegram_id}")
    
    async def set_admin_token(self, telegram_id: int, access_token: str, role: str) -> None:
        """Store admin access token and role."""
        conn = await self._get_connection()
        # Check if credentials exist
        async with conn.execute(
            "SELECT email, password FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
        
        if row:
            # Update existing record
            await conn.execute(
                """UPDATE user_credentials 
                   SET access_token = ?, role = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE telegram_id = ?""",
                (access_token, role, telegram_id)
            )
        else:
            # Insert new record (admin might not have email/password stored)
            await conn.execute(
                """INSERT INTO user_credentials 
                   (telegram_id, email, password, access_token, role, updated_at)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (telegram_id, "", "", access_token, role)
            )
        await conn.commit()
        logger.info(f"💾 Stored admin token for telegram_id {telegram_id}, role: {role}")
    
    async def get_admin_token(self, telegram_id: int) -> Optional[str]:
        """Get admin access token."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT access_token FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["access_token"] if row and row["access_token"] else None
    
    async def get_user_role(self, telegram_id: int) -> Optional[str]:
        """Get user role (admin, agent, player)."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT role FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["role"] if row and row["role"] else None
    
    async def clear_admin_token(self, telegram_id: int) -> None:
        """Clear admin access token (logout)."""
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE user_credentials SET access_token = NULL, role = NULL WHERE telegram_id = ?",
            (telegram_id,)
        )
        await conn.commit()
        logger.info(f"🗑️ Cleared admin token for telegram_id {telegram_id}")
    
    async def get_user_credentials(self, telegram_id: int) -> Optional[Dict[str, str]]:
        """Get stored user credentials."""
        conn = await self._get_connection()
        async with conn.execute(
            "SELECT email, password FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"email": row["email"], "password": row["password"]}
            return None
    
    async def is_user_logged_in(self, telegram_id: int) -> bool:
        """Check if user has stored credentials (is logged in)."""
        credentials = await self.get_user_credentials(telegram_id)
        return credentials is not None
    
    async def clear_user_credentials(self, telegram_id: int) -> None:
        """Clear stored user credentials (logout)."""
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM user_credentials WHERE telegram_id = ?",
            (telegram_id,)
        )
        await conn.commit()
        logger.info(f"🗑️ Cleared credentials for telegram_id {telegram_id}")
    
    async def close(self) -> None:
        """Close storage connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("SQLite storage connection closed")

