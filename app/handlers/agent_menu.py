"""Agent menu handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime, timedelta

from app.services.api_client import APIClient
from app.storage import StorageInterface
from app.utils.text_templates import TextTemplates

logger = logging.getLogger(__name__)

router = Router()


class AgentTransactionStates(StatesGroup):
    """FSM states for agent transaction management."""
    entering_date = State()
    updating_status = State()


async def show_agent_menu(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show agent menu."""
    await state.clear()
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    from app.utils.keyboards import get_web_app_url, is_valid_web_app_url
    
    # Get player UUID if available (agent might have a player profile)
    telegram_id = message.from_user.id
    from app.services.player_service import PlayerService
    player_service = PlayerService(api_client, storage)
    player_uuid = await player_service.get_player_uuid(telegram_id)
    
    web_app_url = get_web_app_url(player_uuid)
    
    # Check if URL is valid for Telegram Web Apps (HTTPS + not localhost)
    can_use_mini_app = is_valid_web_app_url(web_app_url)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    # Get button texts from templates
    button_my_tx = await templates.get_template("button_my_transactions", lang, "📋 My Transactions")
    button_recent = await templates.get_template("button_recent_24h", lang, "🕐 Recent (24h)")
    button_by_date = await templates.get_template("button_by_date", lang, "📅 By Date")
    button_my_stats = await templates.get_template("button_my_stats", lang, "📊 My Stats")
    button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
    button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
    
    # Build first row: mini app button (if valid) + My Transactions
    if can_use_mini_app:
        # Mini app button (web_app) - appears on left side
        mini_app_button = KeyboardButton(
            text="📱 Open App",
            web_app=WebAppInfo(url=web_app_url)
        )
        first_row = [mini_app_button, KeyboardButton(text=button_my_tx)]
    else:
        # Skip mini app button if URL is invalid (HTTP or localhost), just show My Transactions
        first_row = [KeyboardButton(text=button_my_tx)]
    
    # Use reply keyboard for better UX (like admin menu)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            first_row,
            [KeyboardButton(text=button_recent)],
            [KeyboardButton(text=button_by_date)],
            [KeyboardButton(text=button_my_stats)],
            [KeyboardButton(text=button_open_browser)],
            [KeyboardButton(text=button_logout)],
        ],
        resize_keyboard=True
    )
    
    agent_title = await templates.get_template("agent_menu_title", lang, "👤 Agent Panel\n\nSelect an option:")
    await message.answer(agent_title, reply_markup=keyboard)


@router.message(F.text)
async def cmd_my_transactions(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle My Transactions button (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role != "agent":
        return  # Not an agent, let other handlers process it
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_my_tx = await templates.get_template("button_my_transactions", lang, "📋 My Transactions")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_my_tx or message.text == "📋 My Transactions":
        await show_my_transactions_for_message(message, state, api_client, storage)


@router.message(F.text)
async def cmd_recent_transactions(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle Recent (24h) button - works for both admin and agent (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_recent = await templates.get_template("button_recent_24h", lang, "🕐 Recent (24h)")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_recent or message.text == "🕐 Recent (24h)":
        if user_role == "agent":
            # Call agent function
            await show_recent_transactions_for_message(message, state, api_client, storage)
        elif user_role == "admin":
            # Route to admin handler
            from app.handlers.admin_menu import show_recent_transactions_for_message as admin_show_recent
            await admin_show_recent(message, state, api_client, storage)
        else:
            error_msg = await templates.get_template("error_admin_access_required", lang, "❌ Please login as admin or agent to use this feature.")
            await message.answer(error_msg)


@router.message(F.text)
async def cmd_by_date(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle By Date button - works for both admin and agent (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_by_date = await templates.get_template("button_by_date", lang, "📅 By Date")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_by_date or message.text == "📅 By Date":
        if user_role == "agent":
            # Call agent function
            await request_date_for_message(message, state, templates, lang)
        elif user_role == "admin":
            # Route to admin handler
            from app.handlers.admin_menu import request_date_for_message as admin_request_date
            await admin_request_date(message, state, templates, lang)
        else:
            error_msg = await templates.get_template("error_admin_access_required", lang, "❌ Please login as admin or agent to use this feature.")
            await message.answer(error_msg)


@router.message(F.text)
async def cmd_my_stats(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle My Stats button (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_my_stats = await templates.get_template("button_my_stats", lang, "📊 My Stats")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_my_stats or message.text == "📊 My Stats":
        if user_role != "agent":
            error_msg = await templates.get_template("error_agent_access_required", lang, "❌ Agent access required.")
            await message.answer(error_msg)
            return
        
        await show_agent_stats(message, state, api_client, storage)


@router.message(F.text)
async def cmd_agent_web_app(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle web app redirect to browser for agent (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    from app.utils.keyboards import get_browser_url
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role != "agent":
        return  # Don't answer, let other handlers process it
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_open_browser or message.text == "🌐 Open in Browser":
        # Agent gets base URL only (no player ID)
        web_url = get_browser_url(player_uuid=None, user_role="agent")
        
        # Create inline keyboard with URL button (opens in browser)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_open_browser, url=web_url)]
        ])
        
        web_app_msg = await templates.get_template("web_app_description", lang, "🌐 Web App\n\nClick the button below to open the web app in your browser:")
        await message.answer(web_app_msg, reply_markup=keyboard)


@router.message(F.text)
async def cmd_agent_logout(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle agent logout button (works with both English and translated text)."""
    # Don't process if user is in a flow state (deposit, withdraw, login, registration)
    current_state = await state.get_state()
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        return  # Let state-specific handlers process it
    
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
    
    # Check if the message text matches the button (works for both English and translated)
    if message.text == button_logout or message.text == "🚪 Logout":
        if user_role != "agent":
            error_msg = await templates.get_template("error_agent_access_required", lang, "❌ Agent access required.")
            await message.answer(error_msg)
            return
    
    try:
        # Get access token
        access_token = await storage.get_admin_token(telegram_id)
        if access_token:
            # Call logout API
            try:
                await api_client.logout()
            except:
                pass  # Ignore logout API errors
        
        # Clear agent token and credentials
        await storage.clear_admin_token(telegram_id)
        await storage.clear_user_credentials(telegram_id)
        
        logout_success = await templates.get_template("logout_success", lang, "✅ Logged out successfully.")
        await message.answer(logout_success)
        await state.clear()
        
        # Return to start
        from app.handlers.start import cmd_start
        await cmd_start(message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error during agent logout: {e}")
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        error_msg = await templates.get_template("error_generic", lang, "❌ Error during logout. Please try again.")
        await message.answer(error_msg)


async def show_my_transactions_for_message(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show all assigned transactions for agent."""
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role != "agent":
        await message.answer("❌ Agent access required.")
        return
    
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Agent session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching your transactions...")
        
        response = await api_client.get_agent_tasks(
            access_token=access_token,
            page=1,
            limit=100,  # Get more transactions to filter
        )
        
        transactions = response.get("tasks", []) or response.get("transactions", [])
        pagination = response.get("pagination", {})
        
        await processing_msg.delete()
        
        if not transactions:
            await message.answer(
                "📋 My Transactions\n\n"
                "No assigned transactions found.",
                reply_markup=build_agent_back_keyboard()
            )
            return
        
        # Store transactions in state for later use
        transactions_dict = {tx.get("id"): tx for tx in transactions}
        await state.update_data(transactions_cache=transactions_dict)
        
        # Build transaction list
        text = f"📋 My Transactions\n\n"
        text += f"Total: {pagination.get('total', len(transactions))}\n"
        text += f"Page: {pagination.get('page', 1)}/{pagination.get('pages', 1)}\n\n"
        text += "Select a transaction:\n\n"
        
        buttons = []
        for tx in transactions[:10]:  # Show first 10
            tx_type = "💵" if tx.get("type") == "DEPOSIT" else "💸"
            tx_status = tx.get("status", "N/A")
            tx_amount = tx.get("amount", "N/A")
            tx_currency = tx.get("currency", "ETB")
            tx_id = tx.get("id")
            tx_date = tx.get("createdAt", "").split("T")[0] if tx.get("createdAt") else "N/A"
            
            button_text = f"{tx_type} {tx_currency} {tx_amount} - {tx_status} ({tx_date})"
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"agent:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="agent:back")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching agent transactions: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching transactions.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


async def show_recent_transactions_for_message(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show recent transactions (last 24 hours) for agent."""
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role != "agent":
        await message.answer("❌ Agent access required.")
        return
    
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Agent session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching recent transactions...")
        
        # Calculate datetime 24 hours ago (not just date)
        from datetime import timezone
        now = datetime.now(timezone.utc)  # Use UTC for consistent comparison
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Fetch all transactions and filter by date
        response = await api_client.get_agent_tasks(
            access_token=access_token,
            page=1,
            limit=100,  # Get more transactions to filter
        )
        
        transactions = response.get("tasks", []) or response.get("transactions", [])
        
        # Filter transactions from last 24 hours (compare full datetime, not just date)
        recent_transactions = []
        logger.info(f"🕐 Filtering {len(transactions)} transactions for last 24 hours (cutoff: {twenty_four_hours_ago})")
        
        for tx in transactions:
            tx_date_str = tx.get("createdAt")
            if tx_date_str:
                try:
                    # Parse the transaction datetime (API returns UTC with Z suffix)
                    if tx_date_str.endswith("Z"):
                        tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                    else:
                        tx_date = datetime.fromisoformat(tx_date_str)
                    
                    # Ensure both are timezone-aware for comparison
                    if not tx_date.tzinfo:
                        # If no timezone, assume UTC
                        tx_date = tx_date.replace(tzinfo=timezone.utc)
                    
                    # Check if transaction is within last 24 hours
                    if tx_date >= twenty_four_hours_ago:
                        recent_transactions.append(tx)
                        logger.debug(f"✅ Transaction {tx.get('id')} is within 24h: {tx_date} >= {twenty_four_hours_ago}")
                    else:
                        logger.debug(f"⏭️ Transaction {tx.get('id')} is too old: {tx_date} < {twenty_four_hours_ago}")
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing transaction date {tx_date_str}: {e}")
                    pass
        
        logger.info(f"🕐 Found {len(recent_transactions)} transactions in last 24 hours")
        
        await processing_msg.delete()
        
        if not recent_transactions:
            await message.answer(
                "🕐 Recent Transactions (24h)\n\n"
                "No transactions found in the last 24 hours.",
                reply_markup=build_agent_back_keyboard()
            )
            return
        
        # Store transactions in state
        transactions_dict = {tx.get("id"): tx for tx in recent_transactions}
        await state.update_data(transactions_cache=transactions_dict)
        
        # Build transaction list
        text = f"🕐 Recent Transactions (24h)\n\n"
        text += f"Found: {len(recent_transactions)} transaction(s)\n\n"
        text += "Select a transaction:\n\n"
        
        buttons = []
        for tx in recent_transactions[:10]:
            tx_type = "💵" if tx.get("type") == "DEPOSIT" else "💸"
            tx_status = tx.get("status", "N/A")
            tx_amount = tx.get("amount", "N/A")
            tx_currency = tx.get("currency", "ETB")
            tx_id = tx.get("id")
            tx_date = tx.get("createdAt", "").split("T")[0] if tx.get("createdAt") else "N/A"
            
            button_text = f"{tx_type} {tx_currency} {tx_amount} - {tx_status} ({tx_date})"
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"agent:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="agent:back")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching recent transactions.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


async def request_date_for_message(message: Message, state: FSMContext, templates: TextTemplates = None, lang: str = "en"):
    """Request date for filtering transactions (from text message)."""
    if templates is None:
        from app.utils.text_templates import TextTemplates
        # This shouldn't happen, but provide fallback
        templates = TextTemplates(None, None)
        lang = "en"
    
    await state.set_state(AgentTransactionStates.entering_date)
    button_back = await templates.get_template("button_back", lang, "🔙 Back")
    filter_msg = await templates.get_template("admin_filter_by_date", lang, "📅 Filter by Date\n\nPlease enter the date (YYYY-MM-DD):\nExample: 2025-11-08")
    await message.answer(
        filter_msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_back, callback_data="agent:back")]
        ])
    )


@router.message(AgentTransactionStates.entering_date, F.text)
async def show_transactions_by_date(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transactions for a specific date."""
    # Check if user is agent
    telegram_id = message.from_user.id
    user_role = await storage.get_user_role(telegram_id)
    if user_role != "agent":
        await message.answer("❌ Agent access required.")
        await state.clear()
        return
    
    date_str = message.text.strip()
    
    try:
        # Validate date format
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_obj.strftime("%Y-%m-%d")
        end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    except ValueError:
        await message.answer(
            "❌ Invalid date format. Please use YYYY-MM-DD format.\n"
            "Example: 2025-11-08"
        )
        return
    
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Agent session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching transactions...")
        
        # Fetch all transactions and filter by date
        response = await api_client.get_agent_tasks(
            access_token=access_token,
            page=1,
            limit=100,  # Get more transactions to filter
        )
        
        transactions = response.get("tasks", []) or response.get("transactions", [])
        
        # Filter transactions by date
        filtered_transactions = []
        for tx in transactions:
            tx_date_str = tx.get("createdAt")
            if tx_date_str:
                try:
                    tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                    if start_date <= tx_date.strftime("%Y-%m-%d") < end_date:
                        filtered_transactions.append(tx)
                except:
                    pass
        
        await processing_msg.delete()
        
        if not filtered_transactions:
            await message.answer(
                f"📅 Transactions for {start_date}\n\n"
                "No transactions found for this date.",
                reply_markup=build_agent_back_keyboard()
            )
            return
        
        # Store transactions in state
        transactions_dict = {tx.get("id"): tx for tx in filtered_transactions}
        await state.update_data(transactions_cache=transactions_dict)
        
        # Build transaction list
        text = f"📅 Transactions for {start_date}\n\n"
        text += f"Found: {len(filtered_transactions)} transaction(s)\n\n"
        text += "Select a transaction:\n\n"
        
        buttons = []
        for tx in filtered_transactions[:10]:
            tx_type = "💵" if tx.get("type") == "DEPOSIT" else "💸"
            tx_status = tx.get("status", "N/A")
            tx_amount = tx.get("amount", "N/A")
            tx_currency = tx.get("currency", "ETB")
            tx_id = tx.get("id")
            
            button_text = f"{tx_type} {tx_currency} {tx_amount} - {tx_status}"
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"agent:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="agent:back")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error fetching transactions by date: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching transactions.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


async def show_agent_stats(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show agent statistics."""
    telegram_id = message.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Agent session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching statistics...")
        
        stats = await api_client.get_agent_stats(access_token)
        
        await processing_msg.delete()
        
        stats_data = stats.get("stats", {})
        
        text = "📊 My Statistics\n\n"
        text += f"Total Assigned: {stats_data.get('totalAssigned', 0)}\n"
        text += f"Pending: {stats_data.get('pending', 0)}\n"
        text += f"In Progress: {stats_data.get('inProgress', 0)}\n"
        text += f"Completed: {stats_data.get('completed', 0)}\n"
        text += f"Failed: {stats_data.get('failed', 0)}\n"
        
        avg_rating = stats_data.get('averageRating')
        if avg_rating:
            text += f"Average Rating: {avg_rating:.1f}\n"
        
        await message.answer(
            text,
            reply_markup=build_agent_back_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error fetching agent stats: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching statistics.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data.startswith("agent:tx:"))
async def show_transaction_details(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transaction details with action buttons."""
    await callback.answer()
    
    transaction_id = int(callback.data.split(":")[-1])
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Agent session expired. Please login again.")
        return
    
    try:
        # Get transaction from cache or fetch from API
        data = await state.get_data()
        transactions_cache = data.get("transactions_cache", {})
        
        if transaction_id in transactions_cache:
            tx = transactions_cache[transaction_id]
            logger.info(f"📋 Using cached transaction data for ID {transaction_id}")
        else:
            # Transaction not in cache, fetch from API
            logger.info(f"🔄 Transaction {transaction_id} not in cache, fetching from API")
            processing_msg = await callback.message.answer("⏳ Fetching transaction details...")
            
            # Fetch all transactions and find the one we need
            response = await api_client.get_agent_tasks(
                access_token=access_token,
                page=1,
                limit=100,
            )
            
            transactions = response.get("tasks", []) or response.get("transactions", [])
            
            # Find transaction by ID
            tx = None
            for t in transactions:
                if t.get("id") == transaction_id:
                    tx = t
                    break
            
            await processing_msg.delete()
            
            if not tx:
                await callback.message.edit_text(
                    f"❌ Transaction {transaction_id} not found.\n\n"
                    f"Please try refreshing the transaction list."
                )
                return
            
            # Update cache with this transaction
            transactions_cache[transaction_id] = tx
            await state.update_data(transactions_cache=transactions_cache)
            logger.info(f"✅ Fetched and cached transaction {transaction_id}")
        
        # Format transaction details (same as admin menu)
        tx_type = tx.get("type") or tx.get("transactionType") or "N/A"
        tx_status = tx.get("status") or "N/A"
        
        # Handle amount
        tx_amount_raw = tx.get("amount")
        if tx_amount_raw is None:
            tx_amount = "N/A"
        elif isinstance(tx_amount_raw, (int, float)):
            tx_amount = f"{tx_amount_raw:.2f}".rstrip('0').rstrip('.')
        else:
            tx_amount = str(tx_amount_raw)
        
        tx_currency = tx.get("currency") or "ETB"
        tx_uuid = tx.get("transactionUuid") or tx.get("uuid") or tx.get("id") or "N/A"
        
        # Handle date
        tx_date_raw = tx.get("createdAt") or tx.get("created_at") or tx.get("requestedAt") or tx.get("requested_at") or tx.get("date")
        if tx_date_raw:
            try:
                if isinstance(tx_date_raw, str):
                    tx_date = tx_date_raw.split("T")[0] if "T" in tx_date_raw else tx_date_raw
                else:
                    tx_date = str(tx_date_raw)
            except:
                tx_date = "N/A"
        else:
            tx_date = "N/A"
        
        deposit_bank = tx.get("depositBank") or tx.get("deposit_bank") or {}
        withdrawal_bank = tx.get("withdrawalBank") or tx.get("withdrawal_bank") or {}
        betting_site = tx.get("bettingSite") or tx.get("betting_site") or {}
        
        # Additional fields
        withdrawal_address = tx.get("withdrawalAddress") or tx.get("withdrawal_address")
        player_site_id = tx.get("playerSiteId") or tx.get("player_site_id")
        screenshot_url = tx.get("screenshotUrl") or tx.get("screenshot_url")
        agent_notes = tx.get("agentNotes") or tx.get("agent_notes")
        
        text = f"📋 Transaction Details\n\n"
        text += f"ID: {transaction_id}\n"
        text += f"UUID: {tx_uuid}\n"
        text += f"Type: {tx_type}\n"
        text += f"Amount: {tx_currency} {tx_amount}\n"
        text += f"Status: {tx_status}\n"
        text += f"Date: {tx_date}\n\n"
        
        if deposit_bank:
            bank_name = deposit_bank.get("bankName") or deposit_bank.get("bank_name") or deposit_bank.get("name") or "N/A"
            text += f"Deposit Bank: {bank_name}\n"
        if withdrawal_bank:
            bank_name = withdrawal_bank.get("bankName") or withdrawal_bank.get("bank_name") or withdrawal_bank.get("name") or "N/A"
            text += f"Withdrawal Bank: {bank_name}\n"
        if withdrawal_address:
            text += f"Withdrawal Address: {withdrawal_address}\n"
        if betting_site:
            site_name = betting_site.get("name") or betting_site.get("siteName") or "N/A"
            text += f"Betting Site: {site_name}\n"
        if player_site_id:
            text += f"Player Site ID: {player_site_id}\n"
        if agent_notes:
            text += f"Agent Notes: {agent_notes}\n"
        
        # Store transaction ID in state
        await state.update_data(selected_transaction_id=transaction_id)
        
        # Build action buttons (agent can only update status)
        buttons = [
            [InlineKeyboardButton(text="✅ Update Status", callback_data=f"agent:status:{transaction_id}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="agent:back")]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Send transaction details with screenshot as image if available
        if screenshot_url:
            try:
                # Try to send the screenshot as an image (don't include screenshot URL in caption since image is displayed)
                from aiogram.types import URLInputFile
                try:
                    await callback.message.delete()  # Try to delete the previous message
                except:
                    pass  # Ignore if deletion fails (message might be too old)
                
                await callback.message.answer_photo(
                    photo=URLInputFile(screenshot_url),
                    caption=text,  # Text already doesn't include screenshot URL
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not send screenshot as image: {e}, sending as text with link")
                # Fallback: add screenshot link to text and send as text
                fallback_text = text + f"\n📎 Screenshot: <a href=\"{screenshot_url}\">View Image</a>"
                try:
                    await callback.message.edit_text(fallback_text, reply_markup=keyboard, parse_mode="HTML")
                except:
                    # If edit fails, send new message
                    await callback.message.answer(fallback_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing transaction details: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error loading transaction details.\n\n"
            f"Error: {type(e).__name__}"
        )


@router.callback_query(F.data.startswith("agent:status:"))
async def update_status_start(callback: CallbackQuery, state: FSMContext):
    """Start status update process."""
    await callback.answer()
    
    transaction_id = int(callback.data.split(":")[-1])
    
    # Store transaction ID
    await state.update_data(selected_transaction_id=transaction_id)
    await state.set_state(AgentTransactionStates.updating_status)
    
    # Status options (agent can set: IN_PROGRESS, SUCCESS, FAILED)
    buttons = [
        [InlineKeyboardButton(text="🔄 IN_PROGRESS", callback_data=f"agent:set_status:{transaction_id}:IN_PROGRESS")],
        [InlineKeyboardButton(text="✅ SUCCESS", callback_data=f"agent:set_status:{transaction_id}:SUCCESS")],
        [InlineKeyboardButton(text="❌ FAILED", callback_data=f"agent:set_status:{transaction_id}:FAILED")],
        [InlineKeyboardButton(text="🔙 Cancel", callback_data=f"agent:tx:{transaction_id}")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"✅ Update Status\n\n"
        f"Transaction ID: {transaction_id}\n\n"
        f"Select new status:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("agent:set_status:"))
async def update_status_confirm(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Confirm and update transaction status."""
    await callback.answer()
    
    parts = callback.data.split(":")
    transaction_id = int(parts[2])
    status = parts[3]
    
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Agent session expired. Please login again.")
        return
    
    try:
        processing_msg = await callback.message.answer("⏳ Updating status...")
        
        response = await api_client.process_transaction(
            access_token=access_token,
            transaction_id=transaction_id,
            status=status,
        )
        
        await processing_msg.delete()
        
        updated_transaction = response.get("transaction", {})
        new_status = updated_transaction.get("status", status)
        
        # Update cache with updated transaction
        data = await state.get_data()
        transactions_cache = data.get("transactions_cache", {})
        
        # Get existing transaction data if available
        existing_tx = transactions_cache.get(transaction_id, {})
        
        # Merge: existing data first, then updated fields on top
        if existing_tx:
            merged_tx = {**existing_tx, **updated_transaction}
            # Preserve important fields
            for key in ["type", "amount", "currency", "transactionUuid", "createdAt", "requestedAt", 
                        "playerSiteId", "withdrawalAddress", "screenshotUrl", "id", "depositBank", 
                        "withdrawalBank", "bettingSite"]:
                if key not in updated_transaction and key in existing_tx:
                    merged_tx[key] = existing_tx[key]
            transactions_cache[transaction_id] = merged_tx
        else:
            transactions_cache[transaction_id] = updated_transaction
        
        await state.update_data(transactions_cache=transactions_cache)
        logger.info(f"✅ Updated transaction {transaction_id} in cache after status update")
        
        await callback.message.edit_text(
            f"✅ Status Updated Successfully!\n\n"
            f"Transaction ID: {transaction_id}\n"
            f"New Status: {new_status}\n\n"
            f"Transaction status has been updated.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to Transaction", callback_data=f"agent:tx:{transaction_id}")],
                [InlineKeyboardButton(text="🏠 Agent Menu", callback_data="agent:back")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error updating status.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data == "agent:back")
async def back_to_agent_menu(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Go back to agent menu."""
    await callback.answer()
    # Don't clear state completely - preserve transactions_cache if it exists
    current_data = await state.get_data()
    transactions_cache = current_data.get("transactions_cache", {})
    
    # Clear state but preserve cache
    await state.clear()
    if transactions_cache:
        await state.update_data(transactions_cache=transactions_cache)
    
    await show_agent_menu(callback.message, state, api_client, storage)


def build_agent_back_keyboard() -> InlineKeyboardMarkup:
    """Build back to agent menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Agent Menu", callback_data="agent:back")]
    ])

