"""Throttling middleware to prevent spam."""
from typing import Callable, Any, Awaitable
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Throttle user actions to prevent spam."""
    
    def __init__(self, rate_limit: float = 8.0):
        """
        Args:
            rate_limit: Minimum seconds between actions (default: 8 seconds)
        """
        self.rate_limit = rate_limit
        self._last_action: dict[int, datetime] = defaultdict(lambda: datetime.min)
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Check if user is rate limited."""
        user_id = None
        
        # Extract user_id from event
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query:
            user_id = event.callback_query.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        # Check rate limit
        now = datetime.now()
        last_action = self._last_action[user_id]
        
        if (now - last_action).total_seconds() < self.rate_limit:
            elapsed = (now - last_action).total_seconds()
            remaining = self.rate_limit - elapsed
            
            # Don't process action, but don't show error for callbacks
            if hasattr(event, "answer"):
                await event.answer(
                    f"⏳ Please wait {remaining:.1f} seconds before trying again.",
                    show_alert=False
                )
            return
        
        # Update last action time
        self._last_action[user_id] = now
        
        return await handler(event, data)

