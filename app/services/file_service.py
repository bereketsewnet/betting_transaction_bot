"""File service for handling file uploads."""
from pathlib import Path
from typing import Optional
import tempfile
import logging
from app.services.api_client import APIClient
from app.config import config
from app.schemas.api_models import UploadConfigResponse, UploadResponse

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self._upload_config: Optional[UploadConfigResponse] = None
    
    async def get_upload_config(self) -> UploadConfigResponse:
        """Get upload configuration from API."""
        if not self._upload_config:
            self._upload_config = await self.api_client.get_upload_config()
        return self._upload_config
    
    async def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """Validate file before upload."""
        config = await self.get_upload_config()
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > config.maxFileSize:
            max_mb = config.maxFileSize / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_mb:.1f}MB."
        
        # Check file type (basic check by extension)
        # In production, you might want to check MIME type
        allowed_extensions = [".png", ".jpg", ".jpeg"]
        if file_path.suffix.lower() not in allowed_extensions:
            return False, "Invalid file type. Only PNG, JPG, and JPEG files are allowed."
        
        return True, None
    
    async def download_telegram_file(
        self,
        bot,
        file_id: str,
        destination: Optional[Path] = None,
    ) -> Path:
        """Download file from Telegram."""
        file = await bot.get_file(file_id)
        
        if not destination:
            # Create temp file
            suffix = Path(file.file_path).suffix if file.file_path else ".jpg"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            destination = Path(temp_file.name)
            temp_file.close()
        
        await bot.download_file(file.file_path, destination=str(destination))
        return destination
    
    async def upload_file(self, file_path: Path) -> UploadResponse:
        """Upload file to backend."""
        # Validate file
        is_valid, error = await self.validate_file(file_path)
        if not is_valid:
            raise ValueError(error)
        
        try:
            response = await self.api_client.upload_file(file_path)
            return response
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    async def cleanup_file(self, file_path: Path) -> None:
        """Delete temporary file."""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

