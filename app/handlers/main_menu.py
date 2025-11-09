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
    
    # Check if user is logged in (has credentials) to show logout button
    telegram_id = message.from_user.id
    is_logged_in = await storage.is_user_logged_in(telegram_id)
    
    # Get player UUID for web app URL
    from app.services.player_service import PlayerService
    player_service = PlayerService(api_client, storage)
    player_uuid = await player_service.get_player_uuid(telegram_id)
    
    keyboard = build_main_menu_keyboard(show_logout=is_logged_in, player_uuid=player_uuid)
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
        telegram_id = message_or_callback.from_user.id
    else:
        message = message_or_callback
        telegram_id = message.from_user.id
    
    # Check if user is admin or agent - show appropriate menu
    user_role = await storage.get_user_role(telegram_id)
    if user_role == "admin":
        from app.handlers.admin_menu import show_admin_menu
        await show_admin_menu(message, state, api_client, storage)
    elif user_role == "agent":
        from app.handlers.agent_menu import show_agent_menu
        await show_agent_menu(message, state, api_client, storage)
    else:
        await show_main_menu(message, state, api_client, storage)


@router.message(F.text == "💵 Deposit")
async def cmd_deposit(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle deposit command."""
    # Check if user is admin or agent - redirect to appropriate menu
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role == "admin":
        from app.handlers.admin_menu import show_admin_menu
        await message.answer("👑 You are logged in as admin. Use the Admin Panel to manage transactions.")
        await show_admin_menu(message, state, api_client, storage)
        return
    elif user_role == "agent":
        from app.handlers.agent_menu import show_agent_menu
        await message.answer("👤 You are logged in as agent. Use the Agent Panel to manage your assigned transactions.")
        await show_agent_menu(message, state, api_client, storage)
        return
    
    from app.handlers.deposit_flow import start_deposit_flow
    await start_deposit_flow(message, state, api_client, storage)


@router.message(F.text == "💸 Withdraw")
async def cmd_withdraw(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle withdraw command."""
    # Check if user is admin or agent - redirect to appropriate menu
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role == "admin":
        from app.handlers.admin_menu import show_admin_menu
        await message.answer("👑 You are logged in as admin. Use the Admin Panel to manage transactions.")
        await show_admin_menu(message, state, api_client, storage)
        return
    elif user_role == "agent":
        from app.handlers.agent_menu import show_agent_menu
        await message.answer("👤 You are logged in as agent. Use the Agent Panel to manage your assigned transactions.")
        await show_agent_menu(message, state, api_client, storage)
        return
    
    from app.handlers.withdraw_flow import start_withdraw_flow
    await start_withdraw_flow(message, state, api_client, storage)


@router.message(F.text == "📜 History")
async def cmd_history(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle history command."""
    # Check if user is admin or agent - redirect to appropriate menu
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role == "admin":
        from app.handlers.admin_menu import show_admin_menu
        await message.answer("👑 You are logged in as admin. Use the Admin Panel to view all transactions.")
        await show_admin_menu(message, state, api_client, storage)
        return
    elif user_role == "agent":
        from app.handlers.agent_menu import show_agent_menu
        await message.answer("👤 You are logged in as agent. Use the Agent Panel to view your assigned transactions.")
        await show_agent_menu(message, state, api_client, storage)
        return
    
    from app.handlers.history import show_transaction_history
    await show_transaction_history(message, state, api_client, storage)


@router.message(F.text == "🌐 Open in Browser")
async def cmd_web_app(message: Message, api_client: APIClient, storage: StorageInterface):
    """Handle web app redirect to browser."""
    from app.services.player_service import PlayerService
    from app.utils.keyboards import get_web_app_url
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    player_service = PlayerService(api_client, storage)
    telegram_id = message.from_user.id
    player_uuid = await player_service.get_player_uuid(telegram_id)
    
    web_url = get_web_app_url(player_uuid)
    
    # Create inline keyboard with URL button (opens in browser)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Open in Browser", url=web_url)]
    ])
    
    await message.answer(
        f"🌐 Web App\n\n"
        f"Click the button below to open the web app in your browser:",
        reply_markup=keyboard
    )


@router.message(F.text == "ℹ️ Help")
async def cmd_help(message: Message):
    """Handle help command."""
    help_text = """
ℹ️ Help

Available commands:
• /start - Start the bot
• /menu - Show main menu
• /logout - Logout from your account
• /help - Show this help message

Main features:
• 💵 Deposit - Make a deposit transaction
• 💸 Withdraw - Make a withdrawal transaction
• 📜 History - View your transaction history
• 📱 Open App - Open mini app (Telegram Web App)
• 🌐 Open in Browser - Open web app in browser
• 🚪 Logout - Logout and login with another account

For support, please contact the administrator.
    """
    await message.answer(help_text)


@router.message(F.text == "🚪 Logout")
@router.message(F.text == "/logout")
async def cmd_logout(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle logout command."""
    telegram_id = message.from_user.id
    logger.info(f"User {telegram_id} requested logout")
    
    # Check if user has credentials stored
    is_logged_in = await storage.is_user_logged_in(telegram_id)
    if not is_logged_in:
        await message.answer("ℹ️ You are not logged in. Nothing to logout.")
        return
    
    try:
        # Call API logout endpoint
        logger.info(f"🔄 Calling /auth/logout API for user {telegram_id}")
        try:
            await api_client.logout()
            logger.info(f"✅ Logout API success for user {telegram_id}")
        except Exception as e:
            logger.warning(f"⚠️ Logout API error (may be fine if already logged out): {e}")
        
        # Clear stored credentials and admin token
        await storage.clear_user_credentials(telegram_id)
        await storage.clear_admin_token(telegram_id)  # Clear admin token if exists
        logger.info(f"🗑️ Cleared credentials and admin token for user {telegram_id}")
        
        # Clear player UUID if needed (optional, but keeps data clean)
        # await storage.set_player_uuid(telegram_id, None)  # Uncomment if you want to clear UUID too
        
        await state.clear()
        await message.answer(
            "✅ Logout successful!\n\n"
            "You can now:\n"
            "• /start - Login with another account\n"
            "• Continue as guest"
        )
        
        # Show welcome/start options
        from app.handlers.start import cmd_start
        await cmd_start(message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"❌ Logout error for user {telegram_id}: {e}", exc_info=True)
        # Even if API fails, clear local credentials
        try:
            await storage.clear_user_credentials(telegram_id)
            await storage.clear_admin_token(telegram_id)  # Clear admin token if exists
            await message.answer(
                "✅ Logged out locally.\n\n"
                "Note: Backend logout may have failed, but you can still login with another account."
            )
        except:
            await message.answer("❌ Logout failed. Please try again or contact support.")

