"""Helper functions for using templates in handlers."""
from typing import Optional
from app.services.api_client import APIClient
from app.storage import StorageInterface
from app.utils.text_templates import TextTemplates


async def get_user_language(telegram_id: int, storage: StorageInterface) -> str:
    """Get user's language code from storage, default to 'en'."""
    templates = TextTemplates(None, storage)
    return await templates.get_user_language(telegram_id)


async def get_template_text(
    api_client: APIClient,
    storage: StorageInterface,
    telegram_id: int,
    key: str,
    default: str = "",
) -> str:
    """Get template text for a user."""
    templates = TextTemplates(api_client, storage)
    lang = await get_user_language(telegram_id, storage)
    return await templates.get_template(key, lang, default)

