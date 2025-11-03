"""Application configuration management."""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1")
    
    # Webhook Configuration
    USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET_TOKEN: Optional[str] = os.getenv("WEBHOOK_SECRET_TOKEN")
    
    # Backend Integration
    BACKEND_NOTIFY_SECRET: str = os.getenv("BACKEND_NOTIFY_SECRET", "")
    
    # Role IDs for user registration (can be changed in .env)
    ADMIN_ROLE_ID: int = int(os.getenv("ADMIN_ROLE_ID", "7"))
    AGENT_ROLE_ID: int = int(os.getenv("AGENT_ROLE_ID", "8"))
    PLAYER_ROLE_ID: int = int(os.getenv("PLAYER_ROLE_ID", "9"))
    
    # Storage Configuration
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "sqlite")  # sqlite or memory
    DB_PATH: str = os.getenv("DB_PATH", "./data/bot.sqlite")
    
    # File Upload
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "5"))
    MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024
    
    # Application Server
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8443"))
    
    # Admin
    BOT_ADMIN_CHAT_ID: Optional[int] = (
        int(os.getenv("BOT_ADMIN_CHAT_ID")) if os.getenv("BOT_ADMIN_CHAT_ID") else None
    )
    
    # Optional: Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Web App URL
    WEB_APP_URL: str = os.getenv("WEB_APP_URL", "https://your-web-app.com")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL is required")
        if cls.USE_WEBHOOK and not cls.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is required when USE_WEBHOOK=true")
        
        # Ensure data directory exists for SQLite
        if cls.STORAGE_MODE == "sqlite":
            db_path = Path(cls.DB_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)


config = Config()

