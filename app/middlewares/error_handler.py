"""Error handler middleware."""
import logging
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import TelegramObject, Update, ErrorEvent
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Handle errors and log them."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Handle errors."""
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            logger.warning(f"Telegram API error: {e}")
            # Don't propagate Telegram API errors
            return None
        except Exception as e:
            logger.error(f"Unhandled error in handler: {e}", exc_info=True)
            # Try to send error message to user
            if hasattr(event, "message") and event.message:
                try:
                    await event.message.answer(
                        "❌ An unexpected error occurred. Please try again later."
                    )
                except:
                    pass
            raise


async def error_handler(event: ErrorEvent):
    """Global error handler."""
    update_id = event.update.update_id if event.update else "unknown"
    logger.error(f"Update {update_id} caused error: {event.exception}", exc_info=event.exception)

