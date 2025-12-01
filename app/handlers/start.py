"""Start command handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional
import logging

from app.services.api_client import APIClient
from app.services.player_service import PlayerService
from app.utils.keyboards import build_inline_keyboard
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface
from app.config import config

logger = logging.getLogger(__name__)

router = Router()


class RegistrationStates(StatesGroup):
    """FSM states for registration."""
    waiting_for_email = State()  # Email will be used as username
    waiting_for_password = State()
    waiting_for_display_name = State()
    waiting_for_phone = State()


class LoginStates(StatesGroup):
    """FSM states for login."""
    waiting_for_username = State()
    waiting_for_password = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle /start command."""
    await state.clear()
    
    try:
        # Get user's language (default to 'en' for initial message)
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(message.from_user.id)
        
        # Get available languages
        languages = await api_client.get_languages()
        active_languages = [lang for lang in languages if lang.isActive]
        
        if not active_languages:
            error_msg = await templates.get_template("error_no_languages", lang, "No languages available. Please contact support.")
            await message.answer(error_msg)
            return
        
        # Build language selection keyboard
        buttons = [(lang.name, f"lang:{lang.code}") for lang in active_languages]
        keyboard = build_inline_keyboard(buttons, row_width=2)
        
        # Get language selection message from template
        lang_selection_msg = await templates.get_template("start_language_selection", lang, "👋 Welcome! Please select your preferred language:")
        await message.answer(lang_selection_msg, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"❌ Error in /start for user {message.from_user.id}: {e}", exc_info=True)
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error details: {str(e)[:200]}")
        
        # Get error message from template
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(message.from_user.id)
        error_msg = await templates.get_template("error_start_failed", lang, 
            f"❌ An error occurred while starting the bot.\n\nError: {type(e).__name__}\nPlease try again or contact support.")
        error_msg = error_msg.replace("{error_type}", type(e).__name__)
        await message.answer(error_msg)


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle language selection."""
    await callback.answer()
    
    language_code = callback.data.split(":", 1)[1]
    telegram_id = callback.from_user.id
    telegram_username = callback.from_user.username
    
    try:
        # Get or create guest player first (this creates player_uuid)
        player_service = PlayerService(api_client, storage)
        # Create guest player if doesn't exist (this will set player_uuid and language)
        player_uuid = await player_service.get_or_create_guest_player(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            language_code=language_code,
        )
        
        # Get templates with user's language
        templates = TextTemplates(api_client, storage)
        welcome_text = await templates.get_welcome_message(language_code)
        
        # Get button texts from templates
        button_phone_login = await templates.get_template("button_phone_login", language_code, "📱 Login/Register")
        button_email_login = await templates.get_template("button_email_login", language_code, "📧 Login with Email")
        button_guest = await templates.get_template("button_continue_guest", language_code, "👤 Continue as Guest")
        what_to_do = await templates.get_template("start_what_to_do", language_code, "What would you like to do?")
        
        # Show registration options
        buttons = [
            (button_phone_login, "auth:telegram"),
            (button_email_login, "auth:login"),
            (button_guest, "auth:guest"),
        ]
        keyboard = build_inline_keyboard(buttons, row_width=1)
        
        # Only show welcome text if it's not empty, otherwise just show the question
        if welcome_text and welcome_text.strip():
            message_text = f"{welcome_text}\n\n{what_to_do}"
        else:
            message_text = what_to_do
        
        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in language selection: {e}", exc_info=True)
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        error_msg = await templates.get_template("error_generic", lang, "❌ An error occurred. Please try again.")
        await callback.message.edit_text(error_msg)


@router.callback_query(F.data == "auth:guest")
async def continue_as_guest(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle guest continuation."""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    telegram_username = callback.from_user.username
    
    try:
        player_service = PlayerService(api_client, storage)
        language_code = await player_service.get_language(telegram_id) or "en"
        
        # Create guest player
        player_uuid = await player_service.get_or_create_guest_player(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            language_code=language_code,
        )
        
        # Get guest success message from template
        templates = TextTemplates(api_client, storage)
        guest_msg = await templates.get_template("guest_created_success", language_code,
            "✅ You are now using the bot as a guest.\n\nYou can make transactions, but some features may be limited.\nTo access all features, please register.")
        await callback.message.edit_text(guest_msg)
        
        # Import here to avoid circular import
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error creating guest player: {e}")
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        error_msg = await templates.get_template("error_generic", lang, "❌ Failed to create guest account. Please try again.")
        await callback.message.edit_text(error_msg)


@router.callback_query(F.data == "auth:telegram")
async def start_telegram_login(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Start Telegram login flow (request contact)."""
    await callback.answer()
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(callback.from_user.id)
    
    share_text = await templates.get_template("login_share_contact", lang, "📱 Please click the button below to share your contact number for secure login/registration.")
    button_text = await templates.get_template("button_share_contact", lang, "📱 Share Contact")
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    # We can't edit text to show ReplyKeyboardMarkup, must send new message
    # Delete previous message to keep chat clean
    try:
        await callback.message.delete()
    except:
        pass
        
    await callback.message.answer(share_text, reply_markup=keyboard)


@router.message(F.contact)
async def process_contact(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process shared contact for login/registration."""
    contact = message.contact
    telegram_id = message.from_user.id
    
    # Verify contact belongs to user
    if contact.user_id != telegram_id:
        await message.answer("❌ Please share your own contact.")
        return

    logger.info(f"📱 Processing contact for user {telegram_id}: {contact.phone_number}")
    
    # Remove keyboard
    from aiogram.types import ReplyKeyboardRemove
    processing_msg = await message.answer("⏳ Verifying...", reply_markup=ReplyKeyboardRemove())
    
    try:
        login_response = await api_client.telegram_login(
            phone=contact.phone_number,
            telegram_id=telegram_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            username=message.from_user.username
        )
        
        logger.info(f"✅ Telegram login success for user {telegram_id}")
        
        # Copied logic from process_login_password
        # Get player profile using userId from login response
        user_id = login_response.get("user", {}).get("id")
        if not user_id:
            logger.error(f"❌ No user.id in login response for user {telegram_id}")
            await processing_msg.edit_text("❌ Login successful but could not get user ID. Please contact support.")
            return
        
        logger.info(f"📋 Got user ID {user_id} from login response")
        
        # Update processing message
        try:
            await processing_msg.edit_text("⏳ Loading your profile...")
        except Exception:
            # If edit fails (e.g. "message can't be edited"), delete and send new
            try:
                await processing_msg.delete()
            except:
                pass
            processing_msg = await message.answer("⏳ Loading your profile...")
        
        # Check if user is admin
        user_data = login_response.get("user", {})
        user_role = user_data.get("role")
        user_role_id = user_data.get("roleId")
        access_token = login_response.get("accessToken")
        
        is_admin = (user_role == "admin") or (user_role_id == config.ADMIN_ROLE_ID)
        is_agent = (user_role == "agent") or (user_role_id == config.AGENT_ROLE_ID)
        
        # Generate a dummy password since we don't have the real one for local storage
        # Actually, for telegram login, we might not need to store password credentials locally 
        # if we trust the session or if we implement token-based local auth.
        # But existing code uses storage.set_user_credentials(telegram_id, username, password)
        # We can store a marker or just the username, but auto-login relies on it?
        # Let's check main_menu.py: is_logged_in = await storage.is_user_logged_in(telegram_id)
        # SQLiteStorage: checks if credentials exist.
        # If we don't store password, is_logged_in might fail or we might need to change it.
        # For now, let's store "TELEGRAM_LOGIN" as password.
        
        username = user_data.get("username") or user_data.get("email")
        dummy_password = "TELEGRAM_LOGIN_SECURE"
        
        if is_admin:
            # Store admin token and role
            if access_token:
                await storage.set_admin_token(telegram_id, access_token, "admin")
            
            await storage.set_user_credentials(telegram_id, username, dummy_password)
            
            await processing_msg.delete()
            templates = TextTemplates(api_client, storage)
            lang = await templates.get_user_language(telegram_id)
            admin_success = await templates.get_template("admin_redirect_message", lang, "✅ Admin login successful!")
            await message.answer(admin_success)
            
            from app.handlers.admin_menu import show_admin_menu
            await show_admin_menu(message, state, api_client, storage)
            return
        
        if is_agent:
            if access_token:
                await storage.set_admin_token(telegram_id, access_token, "agent")
            
            await storage.set_user_credentials(telegram_id, username, dummy_password)
            
            await processing_msg.delete()
            templates = TextTemplates(api_client, storage)
            lang = await templates.get_user_language(telegram_id)
            agent_success = await templates.get_template("agent_redirect_message", lang, "✅ Agent login successful!")
            await message.answer(agent_success)
            
            from app.handlers.agent_menu import show_agent_menu
            await show_agent_menu(message, state, api_client, storage)
            return
            
        # Regular player
        # Get player profile to ensure we have playerUuid
        player_response = await api_client.get_player_by_user_id(user_id)
        player_uuid = player_response.player.playerUuid
        
        player_service = PlayerService(api_client, storage)
        await player_service.storage.set_player_uuid(telegram_id, player_uuid)
        
        # Store credentials
        await storage.set_user_credentials(telegram_id, username, dummy_password)
        
        await processing_msg.delete()
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        login_success = await templates.get_template("login_success", lang, "✅ Login/Registration successful!")
        await message.answer(login_success)
        
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"❌ Telegram login error: {e}", exc_info=True)
        await processing_msg.edit_text("❌ Login failed. Please try again or use email login.")
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        error_msg = await templates.get_template("error_generic", lang, "❌ An error occurred.")
        await message.answer(error_msg)


@router.callback_query(F.data == "auth:login")
async def start_login(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Start login flow."""
    telegram_id = callback.from_user.id
    logger.info(f"User {telegram_id} started login")
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    # Check if user already has credentials stored (already logged in)
    is_logged_in = await storage.is_user_logged_in(telegram_id)
    if is_logged_in:
        logger.info(f"✅ User {telegram_id} already has credentials stored")
        credentials = await storage.get_user_credentials(telegram_id)
        await callback.answer("ℹ️ You are already logged in!", show_alert=True)
        
        # Use inline keyboard to allow switching accounts
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        button_cancel = await templates.get_template("button_cancel", lang, "❌ Cancel")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Login with Another Account", callback_data="auth:login_switch")],
            [InlineKeyboardButton(text=button_cancel, callback_data="auth:cancel")]
        ])
        
        await callback.message.edit_text(
            "✅ You are already logged in!\n\n"
            f"Email: {credentials.get('email', 'Unknown')}\n\n"
            "Do you want to logout and login with another account?",
            reply_markup=keyboard
        )
        return
    
    await callback.answer()
    await state.set_state(LoginStates.waiting_for_username)
    login_msg = await templates.get_template("login_enter_username", lang, "🔐 Login\n\nPlease enter your username (email):")
    await callback.message.edit_text(login_msg)


@router.message(LoginStates.waiting_for_username, F.text)
async def process_login_username(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process login username input."""
    logger.info(f"📧 User {message.from_user.id} entered username for login")
    username = message.text.strip()
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    
    if not username or len(username) < 3:
        logger.warning(f"❌ Invalid username length from user {message.from_user.id}: {len(username)}")
        error_msg = await templates.get_template("error_validation_failed", lang, "❌ Email must be at least 3 characters. Please try again:")
        await message.answer(error_msg)
        return
    
    logger.info(f"✅ Username saved for user {message.from_user.id}, requesting password")
    await state.update_data(username=username)
    await state.set_state(LoginStates.waiting_for_password)
    new_state = await state.get_state()
    logger.info(f"   State set to: {new_state}")
    logger.info(f"   Expected state: {LoginStates.waiting_for_password}")
    password_msg = await templates.get_template("login_enter_password", lang, "Please enter your password:")
    await message.answer(password_msg)


@router.message(LoginStates.waiting_for_password, F.text)
async def process_login_password(message: Message, state: FSMContext, api_client: APIClient = None, storage: StorageInterface = None):
    """Process login password and complete login."""
    logger.info(f"🔐 Login password handler triggered for user {message.from_user.id}")
    current_state = await state.get_state()
    logger.info(f"   Current State: {current_state}")
    
    # Check if dependencies are available
    if api_client is None or storage is None:
        logger.error(f"❌ Dependencies missing in password handler for user {message.from_user.id}")
        logger.error(f"   api_client: {api_client}, storage: {storage}")
        # Can't use templates here since api_client might be None, use hardcoded fallback
        await message.answer("❌ System error. Please restart with /start")
        return
    
    password = message.text.strip()
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    
    if not password or len(password) < 8:
        logger.warning(f"❌ Invalid password length from user {message.from_user.id}: {len(password)}")
        error_msg = await templates.get_template("error_validation_failed", lang, "❌ Password must be at least 8 characters. Please try again:")
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    
    logger.info(f"📊 State data for user {telegram_id}: {list(data.keys())}")
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    if "username" not in data:
        logger.error(f"❌ No username in state data for user {telegram_id}")
        error_msg = await templates.get_template("error_generic", lang, "❌ Session expired. Please start again with /start")
        await message.answer(error_msg)
        await state.clear()
        return
    
    username = data.get("username", "").strip()
    if not username:
        logger.error(f"❌ Empty username in state data for user {telegram_id}")
        error_msg = await templates.get_template("error_generic", lang, "❌ Username is missing. Please start again with /start")
        await message.answer(error_msg)
        await state.clear()
        return
    
    logger.info(f"🔄 Processing login for user {telegram_id}")
    logger.info(f"   Username: {username}")
    logger.info(f"   Password length: {len(password)}")
    logger.info(f"   Username type: {type(username)}, Password type: {type(password)}")
    
    try:
        # Show processing message
        processing_msg = await message.answer("⏳ Logging in, please wait...")
        
        # Login to backend
        logger.info(f"🔄 Calling /auth/login API for user {telegram_id}")
        login_response = await api_client.login(
            username=username,
            password=password,
        )
        logger.info(f"✅ Login API success for user {telegram_id}")
        logger.debug(f"   Response keys: {list(login_response.keys())}")
        
        # Get player profile using userId from login response
        user_id = login_response.get("user", {}).get("id")
        if not user_id:
            logger.error(f"❌ No user.id in login response for user {telegram_id}")
            await message.answer("❌ Login successful but could not get user ID. Please contact support.")
            await state.clear()
            return
        
        logger.info(f"📋 Got user ID {user_id} from login response")
        
        # Update processing message
        await processing_msg.edit_text("⏳ Loading your profile...")
        
        # Check if user is admin
        user_data = login_response.get("user", {})
        user_role = user_data.get("role")  # String like "admin"
        user_role_id = user_data.get("roleId")  # Integer like 7
        access_token = login_response.get("accessToken")
        
        logger.info(f"📋 User role: {user_role}, roleId: {user_role_id}, User ID: {user_id}")
        
        # If admin, handle differently (no player profile needed)
        is_admin = (user_role == "admin") or (user_role_id == config.ADMIN_ROLE_ID)
        is_agent = (user_role == "agent") or (user_role_id == config.AGENT_ROLE_ID)
        
        if is_admin:
            logger.info(f"👑 Admin login detected for user {telegram_id}")
            
            # Store admin token and role first
            if access_token:
                await storage.set_admin_token(telegram_id, access_token, "admin")
                logger.info(f"💾 Stored admin token for user {telegram_id}")
            
            # Store credentials (this will preserve the admin token we just stored)
            await storage.set_user_credentials(telegram_id, data["username"], password)
            logger.info(f"💾 Stored credentials for user {telegram_id}")
            
            # Verify token is still there
            stored_token = await storage.get_admin_token(telegram_id)
            if stored_token:
                logger.info(f"✅ Verified admin token is stored for user {telegram_id}")
            else:
                logger.warning(f"⚠️ Admin token not found after storing credentials for user {telegram_id}")
            
            # Delete processing message and show success
            await processing_msg.delete()
            templates = TextTemplates(api_client, storage)
            lang = await templates.get_user_language(telegram_id)
            admin_success = await templates.get_template("admin_redirect_message", lang, "✅ Admin login successful! Welcome to Admin Panel!")
            await message.answer(admin_success)
            await state.clear()
            
            # Show admin menu (with error handling for web app button)
            try:
                from app.handlers.admin_menu import show_admin_menu
                await show_admin_menu(message, state, api_client, storage)
            except Exception as menu_error:
                logger.error(f"❌ Error showing admin menu: {menu_error}", exc_info=True)
                # Try to show menu without web app button as fallback
                templates = TextTemplates(api_client, storage)
                lang = await templates.get_user_language(telegram_id)
                admin_success = await templates.get_template("admin_redirect_message", lang, "✅ Admin login successful! Welcome to Admin Panel!")
                await message.answer(
                    f"{admin_success}\n\n"
                    "⚠️ Note: Mini app button is only available with HTTPS URLs.\n"
                    "Use '🌐 Open in Browser' button to access the web app."
                )
                # Show a simple menu without web app
                from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
                simple_keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📋 All Transactions")],
                        [KeyboardButton(text="🕐 Recent (24h)")],
                        [KeyboardButton(text="📅 By Date")],
                        [KeyboardButton(text="🌐 Open in Browser")],
                        [KeyboardButton(text="🚪 Logout")],
                    ],
                    resize_keyboard=True
                )
                templates = TextTemplates(api_client, storage)
                lang = await templates.get_user_language(telegram_id)
                admin_title = await templates.get_template("admin_menu_title", lang, "👑 Admin Panel\n\nSelect an option:")
                await message.answer(admin_title, reply_markup=simple_keyboard)
            return
        
        if is_agent:
            logger.info(f"👤 Agent login detected for user {telegram_id}")
            
            # Store agent token and role first
            if access_token:
                await storage.set_admin_token(telegram_id, access_token, "agent")
                logger.info(f"💾 Stored agent token for user {telegram_id}")
            
            # Store credentials (this will preserve the agent token we just stored)
            await storage.set_user_credentials(telegram_id, data["username"], password)
            logger.info(f"💾 Stored credentials for user {telegram_id}")
            
            # Verify token is still there
            stored_token = await storage.get_admin_token(telegram_id)
            if stored_token:
                logger.info(f"✅ Verified agent token is stored for user {telegram_id}")
            else:
                logger.warning(f"⚠️ Agent token not found after storing credentials for user {telegram_id}")
            
            # Delete processing message and show success
            await processing_msg.delete()
            templates = TextTemplates(api_client, storage)
            lang = await templates.get_user_language(telegram_id)
            agent_success = await templates.get_template("agent_redirect_message", lang, "✅ Agent login successful! Welcome to Agent Panel!")
            await message.answer(agent_success)
            await state.clear()
            
            # Show agent menu (with error handling for web app button)
            try:
                from app.handlers.agent_menu import show_agent_menu
                await show_agent_menu(message, state, api_client, storage)
            except Exception as menu_error:
                logger.error(f"❌ Error showing agent menu: {menu_error}", exc_info=True)
                # Try to show menu without web app button as fallback
                templates = TextTemplates(api_client, storage)
                lang = await templates.get_user_language(telegram_id)
                agent_success = await templates.get_template("agent_redirect_message", lang, "✅ Agent login successful! Welcome to Agent Panel!")
                await message.answer(
                    f"{agent_success}\n\n"
                    "⚠️ Note: Mini app button is only available with HTTPS URLs.\n"
                    "Use '🌐 Open in Browser' button to access the web app."
                )
                # Show a simple menu without web app
                from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
                simple_keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📋 My Transactions")],
                        [KeyboardButton(text="🕐 Recent (24h)")],
                        [KeyboardButton(text="📅 By Date")],
                        [KeyboardButton(text="📊 My Stats")],
                        [KeyboardButton(text="🌐 Open in Browser")],
                        [KeyboardButton(text="🚪 Logout")],
                    ],
                    resize_keyboard=True
                )
                templates = TextTemplates(api_client, storage)
                lang = await templates.get_user_language(telegram_id)
                agent_title = await templates.get_template("agent_menu_title", lang, "👤 Agent Panel\n\nSelect an option:")
                await message.answer(agent_title, reply_markup=simple_keyboard)
            return
        
        # Regular player login - get player profile
        try:
            logger.info(f"🔄 Calling /players/user/{user_id} API")
            player_response = await api_client.get_player_by_user_id(user_id)
            player_uuid = player_response.player.playerUuid
            logger.info(f"✅ Got playerUuid: {player_uuid}")
            
            # Store player UUID
            player_service = PlayerService(api_client, storage)
            await player_service.storage.set_player_uuid(telegram_id, player_uuid)
            logger.info(f"💾 Stored playerUuid for user {telegram_id}")
            
            # Get language if available
            language_code = await player_service.get_language(telegram_id) or "en"
            if language_code:
                await player_service.set_language(telegram_id, language_code)
            
            logger.info(f"🎉 Login complete for user {telegram_id}")
            
            # Store credentials locally so user doesn't need to login again
            await storage.set_user_credentials(telegram_id, data["username"], password)
            logger.info(f"💾 Stored credentials for user {telegram_id}")
            
            # Delete processing message and show success
            await processing_msg.delete()
            templates = TextTemplates(api_client, storage)
            lang = await templates.get_user_language(telegram_id)
            login_success = await templates.get_template("login_success", lang, "✅ Login successful! Welcome back to Betting Payment Manager!")
            await message.answer(login_success)
            await state.clear()
            
            # Show main menu
            try:
                from app.handlers.main_menu import show_main_menu
                await show_main_menu(message, state, api_client, storage)
            except Exception as menu_error:
                logger.error(f"❌ Error showing main menu: {menu_error}", exc_info=True)
                # Show fallback menu
                await message.answer("✅ Login successful! Welcome back to Betting Payment Manager!")
                from app.handlers.main_menu import show_main_menu
                await show_main_menu(message, state, api_client, storage)
            
        except Exception as e:
            logger.error(f"❌ Error getting player after login: {e}", exc_info=True)
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error details: {str(e)}")
            
            # Delete processing message
            await processing_msg.delete()
            
            await message.answer(
                "⚠️ Login successful, but player profile not found.\n\n"
                "You can continue as guest. To link your account, please register first."
            )
            await state.clear()
            
            # Continue as guest
            player_service = PlayerService(api_client, storage)
            await player_service.get_or_create_guest_player(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                language_code="en",
            )
            from app.handlers.main_menu import show_main_menu
            await show_main_menu(message, state, api_client, storage)
            
    except Exception as e:
        logger.error(f"❌ Login API error for user {telegram_id}: {e}", exc_info=True)
        logger.error(f"   Error type: {type(e).__name__}")
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Parse error message
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        
        error_str = str(e).lower()
        if "invalid credentials" in error_str or "401" in error_str:
            error_msg = await templates.get_template("login_failed", lang, "❌ Login failed. Invalid email or password.")
            logger.warning(f"   Invalid credentials for {data.get('username')}")
        elif "400" in error_str or "validation" in error_str:
            error_msg = await templates.get_template("error_validation_failed", lang, "❌ Login failed. Invalid input format.")
            logger.warning(f"   Validation error for {data.get('username')}")
        elif "404" in error_str:
            error_msg = await templates.get_template("error_transaction_not_found", lang, "❌ Login failed. Account not found.")
            logger.warning(f"   Account not found for {data.get('username')}")
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            error_msg = await templates.get_template("error_generic", lang, "❌ Login failed. Server error. Please try again later.")
            logger.error(f"   Server error")
        elif "connection" in error_str or "timeout" in error_str:
            error_msg = await templates.get_template("error_connection_failed", lang, "❌ Login failed. Cannot connect to server. Please try again.")
            logger.error(f"   Connection error")
        else:
            error_msg = await templates.get_template("login_failed", lang, f"❌ Login failed. An error occurred. Please try again later.")
            logger.error(f"   Unknown error: {str(e)[:100]}")
        
        await message.answer(error_msg)
        await state.clear()
        retry_msg = await templates.get_template("error_generic", lang, "Please try /start again to login or register.")
        await message.answer(retry_msg)


@router.callback_query(F.data == "auth:login_switch")
async def switch_login_account(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Logout and start login with another account."""
    telegram_id = callback.from_user.id
    logger.info(f"User {telegram_id} wants to switch account")
    
    await callback.answer()
    
    # Logout from API
    try:
        logger.info(f"🔄 Calling /auth/logout API for user {telegram_id}")
        await api_client.logout()
        logger.info(f"✅ Logout API success for user {telegram_id}")
    except Exception as e:
        logger.warning(f"⚠️ Logout API error (may be fine if already logged out): {e}")
    
    # Clear stored credentials
    await storage.clear_user_credentials(telegram_id)
    logger.info(f"🗑️ Cleared credentials for user {telegram_id}")
    
    await state.clear()
    
    await callback.message.edit_text(
        "🔄 Switching account...\n\n"
        "Please enter your email address:"
    )
    
    # Start login flow
    await state.set_state(LoginStates.waiting_for_username)


@router.callback_query(F.data == "auth:cancel")
async def cancel_login_switch(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Cancel login switch and show main menu."""
    await callback.answer()
    await state.clear()
    
    from app.handlers.main_menu import show_main_menu
    await show_main_menu(callback.message, state, api_client, storage)


@router.callback_query(F.data == "auth:register")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    """Start registration flow."""
    logger.info(f"User {callback.from_user.id} started registration")
    await callback.answer()
    await state.set_state(RegistrationStates.waiting_for_email)
    await callback.message.edit_text(
        "📝 Registration\n\n"
        "Let's create your account. Please enter your email address:"
    )


@router.message(RegistrationStates.waiting_for_email, F.text)
async def process_email(message: Message, state: FSMContext):
    """Process email input (will be used as both email and username)."""
    logger.info(f"📧 User {message.from_user.id} entered email for registration")
    from app.utils.validators import validate_email
    email = message.text.strip()
    is_valid, error = validate_email(email)
    if not is_valid:
        logger.warning(f"❌ Invalid email from user {message.from_user.id}: {error}")
        await message.answer(f"❌ {error}. Please try again:")
        return
    
    logger.info(f"✅ Valid email for user {message.from_user.id}, requesting password")
    # Email will be used as both username and email
    await state.update_data(email=email, username=email)
    await state.set_state(RegistrationStates.waiting_for_password)
    await message.answer("🔒 Please enter your password (minimum 8 characters):")


@router.message(RegistrationStates.waiting_for_password, F.text)
async def process_password(message: Message, state: FSMContext):
    """Process password input."""
    logger.info(f"🔐 User {message.from_user.id} entered password for registration")
    password = message.text.strip()
    if len(password) < 8:
        logger.warning(f"❌ Password too short from user {message.from_user.id}: {len(password)} chars")
        await message.answer("❌ Password must be at least 8 characters. Please try again:")
        return
    
    logger.info(f"✅ Valid password for user {message.from_user.id}, requesting display name")
    await state.update_data(password=password)
    await state.set_state(RegistrationStates.waiting_for_display_name)
    await message.answer("👤 Please enter your display name:")


@router.message(RegistrationStates.waiting_for_display_name, F.text)
async def process_display_name(message: Message, state: FSMContext):
    """Process display name input."""
    logger.info(f"👤 User {message.from_user.id} entered display name for registration")
    display_name = message.text.strip()
    if not display_name or len(display_name) < 2:
        logger.warning(f"❌ Display name too short from user {message.from_user.id}: {len(display_name)} chars")
        await message.answer("❌ Display name must be at least 2 characters. Please try again:")
        return
    
    logger.info(f"✅ Valid display name for user {message.from_user.id}, requesting phone")
    await state.update_data(display_name=display_name)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer("📱 Please enter your phone number (required, format: +1234567890):")


@router.message(RegistrationStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process phone input and complete registration."""
    logger.info(f"📱 User {message.from_user.id} processing phone number")
    
    # Phone is now REQUIRED - validate it
    from app.utils.validators import validate_phone
    phone_text = message.text.strip()
    
    # Don't allow /skip for phone anymore
    if phone_text == "/skip":
        logger.warning(f"❌ User {message.from_user.id} tried to skip phone (not allowed)")
        await message.answer("❌ Phone number is required for registration. Please enter your phone number (format: +1234567890):")
        return
    
    is_valid, error = validate_phone(phone_text)
    if not is_valid:
        logger.warning(f"❌ Invalid phone from user {message.from_user.id}: {error}")
        await message.answer(f"❌ {error}. Please enter a valid phone number (format: +1234567890):")
        return
    
    phone = phone_text
    logger.info(f"✅ Valid phone for user {message.from_user.id}: {phone}")
    
    data = await state.get_data()
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    
    logger.info(f"📊 Registration data for user {telegram_id}:")
    logger.info(f"   Email/Username: {data.get('email')}")
    logger.info(f"   Display Name: {data.get('display_name')}")
    logger.info(f"   Phone: {phone}")  # Phone is now always present (required)
    
    try:
        # Show processing message
        processing_msg = await message.answer("⏳ Creating your account, please wait...")
        
        player_service = PlayerService(api_client, storage)
        language_code = await player_service.get_language(telegram_id) or "en"
        
        logger.info(f"🔄 Calling register_player API for user {telegram_id}")
        player_uuid = await player_service.register_player(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            language_code=language_code,
            username=data["username"],  # Email used as username
            email=data["email"],
            password=data["password"],
            display_name=data["display_name"],
            phone=phone,
        )
        
        logger.info(f"✅ Registration successful for user {telegram_id}, playerUuid: {player_uuid}")
        
        # Delete processing message and show success
        await processing_msg.delete()
        await message.answer("✅ Registration successful! Welcome to Betting Payment Manager!")
        await state.clear()
        
        # Import here to avoid circular import
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"❌ Registration error for user {telegram_id}: {e}", exc_info=True)
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Parse error message
        error_msg = "❌ Registration failed. "
        error_str = str(e).lower()
        
        if "already exists" in error_str or "409" in error_str:
            error_msg += "This email is already registered. Try logging in instead."
        elif "400" in error_str or "validation" in error_str:
            error_msg += "Invalid input format."
        else:
            error_msg += "Please try again or contact support."
        
        await message.answer(error_msg)
        await state.clear()


@router.message(RegistrationStates.waiting_for_phone, F.text == "/skip")
async def skip_phone(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle /skip command in registration - phone is now required, so this will show an error."""
    logger.warning(f"❌ User {message.from_user.id} tried to skip phone (required) in registration")
    await message.answer("❌ Phone number is required for registration. Please enter your phone number (format: +1234567890):")

