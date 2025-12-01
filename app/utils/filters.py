"""Custom filters for aiogram handlers."""
from __future__ import annotations

from typing import ClassVar, Iterable, Set

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.storage import StorageInterface


class RoleFilter(BaseFilter):
    """Filter messages based on the user's stored role."""
    
    default_storage: ClassVar[StorageInterface | None] = None
    
    @classmethod
    def configure(cls, storage: StorageInterface) -> None:
        cls.default_storage = storage

    def __init__(self, include: Iterable[str] | None = None, exclude: Iterable[str] | None = None):
        self.include: Set[str] = set(include or [])
        self.exclude: Set[str] = set(exclude or [])

    async def __call__(
        self,
        message: Message,
        storage: StorageInterface | None = None,
        **kwargs,
    ) -> bool:
        storage = storage or kwargs.get("storage") or self.default_storage
        if storage is None:
            raise RuntimeError("RoleFilter storage not configured")

        role = await storage.get_user_role(message.from_user.id)

        if self.include and role not in self.include:
            return False

        if self.exclude and role in self.exclude:
            return False

        return True

