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
        # Get available languages
        languages = await api_client.get_languages()
        active_languages = [lang for lang in languages if lang.isActive]
        
        if not active_languages:
            await message.answer("No languages available. Please contact support.")
            return
        
        # Build language selection keyboard
        buttons = [(lang.name, f"lang:{lang.code}") for lang in active_languages]
        keyboard = build_inline_keyboard(buttons, row_width=2)
        
        await message.answer(
            "👋 Welcome! Please select your preferred language:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.answer("❌ An error occurred. Please try again later.")


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
        
        # Get welcome message
        templates = TextTemplates(api_client)
        welcome_text = await templates.get_welcome_message(language_code)
        
        # Show registration options
        buttons = [
            ("📝 Register", "auth:register"),
            ("🔐 Login", "auth:login"),
            ("👤 Continue as Guest", "auth:guest"),
        ]
        keyboard = build_inline_keyboard(buttons, row_width=1)
        
        await callback.message.edit_text(
            f"{welcome_text}\n\nWhat would you like to do?",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in language selection: {e}", exc_info=True)
        await callback.message.edit_text("❌ An error occurred. Please try again.")


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
        
        await callback.message.edit_text(
            "✅ You are now using the bot as a guest.\n\n"
            "You can make transactions, but some features may be limited.\n"
            "To access all features, please register."
        )
        
        # Import here to avoid circular import
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error creating guest player: {e}")
        await callback.message.edit_text("❌ Failed to create guest account. Please try again.")


@router.callback_query(F.data == "auth:login")
async def start_login(callback: CallbackQuery, state: FSMContext):
    """Start login flow."""
    logger.info(f"User {callback.from_user.id} started login")
    await callback.answer()
    await state.set_state(LoginStates.waiting_for_username)
    await callback.message.edit_text(
        "🔐 Login\n\n"
        "Please enter your email address:"
    )


@router.message(LoginStates.waiting_for_username, F.text)
async def process_login_username(message: Message, state: FSMContext):
    """Process login username input."""
    logger.info(f"📧 User {message.from_user.id} entered username for login")
    username = message.text.strip()
    if not username or len(username) < 3:
        logger.warning(f"❌ Invalid username length from user {message.from_user.id}: {len(username)}")
        await message.answer("❌ Email must be at least 3 characters. Please try again:")
        return
    
    logger.info(f"✅ Username saved for user {message.from_user.id}, requesting password")
    await state.update_data(username=username)
    await state.set_state(LoginStates.waiting_for_password)
    new_state = await state.get_state()
    logger.info(f"   State set to: {new_state}")
    logger.info(f"   Expected state: {LoginStates.waiting_for_password}")
    await message.answer("🔒 Please enter your password:")


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
        await message.answer("❌ System error. Please restart with /start")
        return
    
    password = message.text.strip()
    if not password or len(password) < 8:
        logger.warning(f"❌ Invalid password length from user {message.from_user.id}: {len(password)}")
        await message.answer("❌ Password must be at least 8 characters. Please try again:")
        return
    
    data = await state.get_data()
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    
    logger.info(f"📊 State data for user {telegram_id}: {list(data.keys())}")
    
    if "username" not in data:
        logger.error(f"❌ No username in state data for user {telegram_id}")
        await message.answer("❌ Session expired. Please start again with /start")
        await state.clear()
        return
    
    logger.info(f"🔄 Processing login for user {telegram_id} with username {data.get('username')}")
    
    try:
        # Login to backend
        logger.info(f"🔄 Calling /auth/login API for user {telegram_id}")
        login_response = await api_client.login(
            username=data["username"],
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
        
        # Get player by user ID to get playerUuid
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
            await message.answer(
                "✅ Login successful! Welcome back to Betting Payment Manager!"
            )
            await state.clear()
            
            # Show main menu
            from app.handlers.main_menu import show_main_menu
            await show_main_menu(message, state, api_client, storage)
            
        except Exception as e:
            logger.error(f"❌ Error getting player after login: {e}", exc_info=True)
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error details: {str(e)}")
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
        
        # Parse error message
        error_msg = "❌ Login failed. "
        error_str = str(e).lower()
        
        if "invalid credentials" in error_str or "401" in error_str:
            error_msg += "Invalid email or password."
            logger.warning(f"   Invalid credentials for {data.get('username')}")
        elif "400" in error_str or "validation" in error_str:
            error_msg += "Invalid input format."
            logger.warning(f"   Validation error for {data.get('username')}")
        elif "404" in error_str:
            error_msg += "Account not found."
            logger.warning(f"   Account not found for {data.get('username')}")
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            error_msg += "Server error. Please try again later."
            logger.error(f"   Server error")
        elif "connection" in error_str or "timeout" in error_str:
            error_msg += "Cannot connect to server. Please try again."
            logger.error(f"   Connection error")
        else:
            error_msg += "An error occurred. Please try again later."
            logger.error(f"   Unknown error: {str(e)[:100]}")
        
        await message.answer(error_msg)
        await state.clear()
        await message.answer("Please try /start again to login or register.")


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
    await message.answer("📱 Please enter your phone number (optional, format: +1234567890) or send /skip:")


@router.message(RegistrationStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process phone input and complete registration."""
    logger.info(f"📱 User {message.from_user.id} processing phone number")
    phone = None
    if message.text and message.text.strip() != "/skip":
        from app.utils.validators import validate_phone
        phone_text = message.text.strip()
        is_valid, error = validate_phone(phone_text)
        if not is_valid:
            logger.warning(f"❌ Invalid phone from user {message.from_user.id}: {error}")
            await message.answer(f"❌ {error}. Please try again or send /skip:")
            return
        phone = phone_text
        logger.info(f"✅ Valid phone for user {message.from_user.id}")
    else:
        logger.info(f"⏭️ User {message.from_user.id} skipped phone number")
    
    data = await state.get_data()
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    
    logger.info(f"📊 Registration data for user {telegram_id}:")
    logger.info(f"   Email/Username: {data.get('email')}")
    logger.info(f"   Display Name: {data.get('display_name')}")
    logger.info(f"   Phone: {phone or 'None'}")
    
    try:
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
        await message.answer("✅ Registration successful! Welcome to Betting Payment Manager!")
        await state.clear()
        
        # Import here to avoid circular import
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"❌ Registration error for user {telegram_id}: {e}", exc_info=True)
        await message.answer("❌ Registration failed. Please try again or contact support.")
        await state.clear()


@router.message(F.text == "/skip")
async def skip_phone(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Skip phone number input."""
    logger.info(f"⏭️ User {message.from_user.id} used /skip command in state {await state.get_state()}")
    if await state.get_state() == RegistrationStates.waiting_for_phone:
        await process_phone(message, state, api_client, storage)

