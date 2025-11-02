"""Main menu handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Optional
import logging

from app.services.api_client import APIClient
from app.utils.keyboards import build_main_menu_keyboard
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface
from app.config import config

logger = logging.getLogger(__name__)

router = Router()


async def show_main_menu(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show main menu."""
    await state.clear()
    
    keyboard = build_main_menu_keyboard()
    await message.answer(
        "🏠 Main Menu\n\n"
        "Select an option:",
        reply_markup=keyboard
    )


@router.message(F.text == "🏠 Main Menu")
@router.message(F.text == "/menu")
@router.callback_query(F.data == "back:main")
async def cmd_main_menu(message_or_callback, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle main menu command."""
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer()
        message = message_or_callback.message
    else:
        message = message_or_callback
    
    await show_main_menu(message, state, api_client, storage)


@router.message(F.text == "💵 Deposit")
async def cmd_deposit(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle deposit command."""
    from app.handlers.deposit_flow import start_deposit_flow
    await start_deposit_flow(message, state, api_client, storage)


@router.message(F.text == "💸 Withdraw")
async def cmd_withdraw(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle withdraw command."""
    from app.handlers.withdraw_flow import start_withdraw_flow
    await start_withdraw_flow(message, state, api_client, storage)


@router.message(F.text == "📜 History")
async def cmd_history(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle history command."""
    from app.handlers.history import show_transaction_history
    await show_transaction_history(message, state, api_client, storage)


@router.message(F.text == "🌐 Open Web App")
async def cmd_web_app(message: Message, api_client: APIClient, storage: StorageInterface):
    """Handle web app redirect."""
    from app.services.player_service import PlayerService
    
    player_service = PlayerService(api_client, storage)
    telegram_id = message.from_user.id
    player_uuid = await player_service.get_player_uuid(telegram_id)
    
    web_url = config.WEB_APP_URL
    if player_uuid:
        web_url = f"{web_url}?playerUuid={player_uuid}"
    
    await message.answer(
        f"🌐 Opening web app...\n\n"
        f"Click the link below to access the full web interface:\n"
        f"{web_url}",
        disable_web_page_preview=False
    )


@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Handle help command."""
    help_text = """
ℹ️ Help

Available commands:
• /start - Start the bot
• /menu - Show main menu
• /help - Show this help message

Main features:
• 💵 Deposit - Make a deposit transaction
• 💸 Withdraw - Make a withdrawal transaction
• 📜 History - View your transaction history
• 🌐 Open Web App - Access full web interface

For support, please contact the administrator.
    """
    await message.answer(help_text)

