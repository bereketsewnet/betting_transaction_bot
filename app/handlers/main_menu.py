"""Main menu handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from app.services.api_client import APIClient
from app.utils.keyboards import build_main_menu_keyboard
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface

logger = logging.getLogger(__name__)

router = Router()


async def show_main_menu(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show main menu with keyboard."""
    telegram_id = message.from_user.id
    
    # Check if user is logged in
    is_logged_in = await storage.is_user_logged_in(telegram_id)
    player_uuid = None
    
    if is_logged_in:
        player_uuid = await storage.get_player_uuid(telegram_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    # Build keyboard with translated buttons
    try:
        keyboard = await build_main_menu_keyboard(show_logout=is_logged_in, player_uuid=player_uuid, templates=templates, lang=lang)
        menu_title = await templates.get_template("main_menu_title", lang, "🏠 Main Menu\n\nSelect an option:")
        await message.answer(menu_title, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error building menu keyboard: {e}")
        # Fallback keyboard
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
        from app.config import config
        
        button_deposit = await templates.get_template("button_deposit", lang, "💵 Deposit")
        button_withdraw = await templates.get_template("button_withdraw", lang, "💸 Withdraw")
        button_history = await templates.get_template("button_history", lang, "📜 History")
        button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
        button_help = await templates.get_template("button_help", lang, "ℹ️ Help")
        button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=button_deposit), KeyboardButton(text=button_withdraw)],
                [KeyboardButton(text=button_history)],
                [KeyboardButton(text=button_open_browser)],
                [KeyboardButton(text=button_help), KeyboardButton(text=button_logout) if is_logged_in else KeyboardButton(text="")]
            ],
            resize_keyboard=True
        )
        menu_title = await templates.get_template("main_menu_title", lang, "🏠 Main Menu\n\nSelect an option:")
        await message.answer(menu_title, reply_markup=keyboard)


@router.message(F.text == "🏠 Main Menu")
@router.message(F.text == "/menu")
@router.callback_query(F.data == "back:main")
async def cmd_main_menu(message_or_callback, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle main menu command or callback."""
    # Clear any active state
    await state.clear()
    
    if isinstance(message_or_callback, CallbackQuery):
        message = message_or_callback.message
        await message_or_callback.answer()
    else:
        message = message_or_callback
    
    telegram_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    user_role = await storage.get_user_role(telegram_id)
    
    # Redirect to appropriate menu based on role
    if user_role == "admin":
        from app.handlers.admin_menu import show_admin_menu
        await show_admin_menu(message, state, api_client, storage)
    elif user_role == "agent":
        from app.handlers.agent_menu import show_agent_menu
        await show_agent_menu(message, state, api_client, storage)
    else:
        await show_main_menu(message, state, api_client, storage)


@router.message(F.text)
async def handle_menu_buttons(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Single handler for all menu button clicks - dispatches to correct function."""
    telegram_id = message.from_user.id
    text = message.text
    
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:", "AdminTransactionStates:", "AgentTransactionStates:"]):
        return  # Let state-specific handlers process it
    
    # Get user's language and button texts
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    # Fetch all button texts
    button_deposit = await templates.get_template("button_deposit", lang, "💵 Deposit")
    button_withdraw = await templates.get_template("button_withdraw", lang, "💸 Withdraw")
    button_history = await templates.get_template("button_history", lang, "📜 History")
    button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
    button_help = await templates.get_template("button_help", lang, "ℹ️ Help")
    button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
    
    # Dispatch based on button text
    if text in [button_deposit, "💵 Deposit"]:
        logger.info(f"✅ Deposit button clicked by user {telegram_id}")
        from app.handlers.deposit_flow import start_deposit_flow
        await start_deposit_flow(message, state, api_client, storage)
    
    elif text in [button_withdraw, "💸 Withdraw"]:
        logger.info(f"✅ Withdraw button clicked by user {telegram_id}")
        from app.handlers.withdraw_flow import start_withdraw_flow
        await start_withdraw_flow(message, state, api_client, storage)
    
    elif text in [button_history, "📜 History"]:
        logger.info(f"✅ History button clicked by user {telegram_id}")
        from app.handlers.history import show_transaction_history
        await show_transaction_history(message, state, api_client, storage)
    
    elif text in [button_open_browser, "🌐 Open in Browser"]:
        logger.info(f"✅ Open in Browser button clicked by user {telegram_id}")
        from app.services.player_service import PlayerService
        from app.utils.keyboards import get_browser_url
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        player_service = PlayerService(api_client, storage)
        player_uuid = await player_service.get_player_uuid(telegram_id)
        
        if player_uuid:
            browser_url = get_browser_url(player_uuid)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 Open Web App", url=browser_url)]
            ])
            
            web_app_msg = await templates.get_template("web_app_description", lang, "🌐 Web App\n\nClick the button below to open the web app in your browser:")
            await message.answer(web_app_msg, reply_markup=keyboard)
        else:
            error_msg = await templates.get_template("error_player_not_found", lang, "❌ Player not found. Please contact support.")
            await message.answer(error_msg)
    
    elif text in [button_help, "ℹ️ Help"]:
        logger.info(f"✅ Help button clicked by user {telegram_id}")
        help_text = await templates.get_template("help_text", lang, """ℹ️ Help

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

For support, please contact the administrator.""")
        await message.answer(help_text)
    
    elif text in [button_logout, "🚪 Logout", "/logout"]:
        logger.info(f"✅ Logout button clicked by user {telegram_id}")
        
        # Check if user has credentials stored
        is_logged_in = await storage.is_user_logged_in(telegram_id)
        if not is_logged_in:
            no_creds_msg = await templates.get_template("logout_not_logged_in", lang, "You are not logged in.")
            await message.answer(no_creds_msg)
            return
        
        # Call logout API
        try:
            await api_client.logout(telegram_id)
            logger.info(f"✅ Logout API success for user {telegram_id}")
        except Exception as e:
            logger.warning(f"Logout API failed (continuing anyway): {e}")
        
        # Clear credentials from storage
        await storage.clear_user_credentials(telegram_id)
        await storage.clear_admin_token(telegram_id)
        logger.info(f"🗑️ Cleared credentials for user {telegram_id}")
        
        # Show logged out message
        logged_out_msg = await templates.get_template("logout_success", lang, "✅ You have been logged out successfully.")
        await message.answer(logged_out_msg)
        
        # Clear state and restart
        await state.clear()
        
        # Show start screen
        from app.handlers.start import cmd_start
        await cmd_start(message, state, api_client, storage)
