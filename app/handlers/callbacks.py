"""General callback handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle cancel callback."""
    await callback.answer("Cancelled")
    await state.clear()
    await callback.message.edit_text("❌ Operation cancelled.")

