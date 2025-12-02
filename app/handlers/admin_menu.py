"""Admin menu handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime, timedelta

from app.services.api_client import APIClient
from app.storage import StorageInterface
from app.utils.text_templates import TextTemplates
from app.utils.filters import RoleFilter
from aiogram.filters import StateFilter

logger = logging.getLogger(__name__)

router = Router()


class AdminTransactionStates(StatesGroup):
    """FSM states for admin transaction management."""
    selecting_filter = State()
    entering_date = State()
    selecting_transaction = State()
    assigning_agent = State()
    updating_status = State()


async def show_admin_menu(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show admin menu."""
    await state.clear()
    
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    from app.utils.keyboards import get_web_app_url, is_valid_web_app_url
    
    # Get player UUID if available (admin might have a player profile)
    telegram_id = message.from_user.id
    from app.services.player_service import PlayerService
    player_service = PlayerService(api_client, storage)
    player_uuid = await player_service.get_player_uuid(telegram_id)
    
    web_app_url = get_web_app_url(player_uuid)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    
    # Get button texts from templates
    button_all_tx = await templates.get_template("button_all_transactions", lang, "📋 All Transactions")
    button_recent = await templates.get_template("button_recent_24h", lang, "🕐 Recent (24h)")
    button_by_date = await templates.get_template("button_by_date", lang, "📅 By Date")
    button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
    button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
    
    # Check if URL is valid for Telegram Web Apps (HTTPS + not localhost)
    can_use_mini_app = is_valid_web_app_url(web_app_url)
    
    # Build first row: mini app button (if valid) + All Transactions
    if can_use_mini_app:
        # Mini app button (web_app) - appears on left side
        mini_app_button = KeyboardButton(
            text="📱 Open App",
            web_app=WebAppInfo(url=web_app_url)
        )
        first_row = [mini_app_button, KeyboardButton(text=button_all_tx)]
    else:
        # Skip mini app button if URL is invalid (HTTP or localhost), just show All Transactions
        first_row = [KeyboardButton(text=button_all_tx)]
    
    # Use reply keyboard for better UX (like main menu)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            first_row,
            [KeyboardButton(text=button_recent)],
            [KeyboardButton(text=button_by_date)],
            [KeyboardButton(text=button_open_browser)],
            [KeyboardButton(text=button_logout)],
        ],
        resize_keyboard=True
    )
    
    admin_title = await templates.get_template("admin_menu_title", lang, "👑 Admin Panel\n\nSelect an option:")
    await message.answer(admin_title, reply_markup=keyboard)


@router.message(RoleFilter(include={"admin"}), F.text, ~StateFilter(AdminTransactionStates))
async def handle_admin_menu_buttons(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Consolidated handler for all admin menu buttons."""
    telegram_id = message.from_user.id
    text = message.text
    current_state = await state.get_state()
    
    logger.info(f"🔍 ADMIN HANDLER CALLED: '{text}' from user {telegram_id}, state: {current_state}")
    
    # Don't process if user is in a flow state
    if current_state and any(current_state.startswith(prefix) for prefix in ["DepositStates:", "WithdrawStates:", "LoginStates:", "RegistrationStates:"]):
        logger.info(f"⏭️ Skipping - user in flow state: {current_state}")
        return
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(telegram_id)
    button_all_tx = await templates.get_template("button_all_transactions", lang, "📋 All Transactions")
    button_recent = await templates.get_template("button_recent_24h", lang, "🕐 Recent (24h)")
    button_by_date = await templates.get_template("button_by_date", lang, "📅 By Date")
    button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
    button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
    
    logger.info(f"🔍 Admin menu button click: '{text}' from user {telegram_id} (role: admin)")
    
    if text == "📋 All Transactions" or text == button_all_tx:
        logger.info(f"✅ Matched: All Transactions")
        await show_all_transactions_for_message(message, state, api_client, storage)
    elif text == "🕐 Recent (24h)" or text == button_recent:
        logger.info(f"✅ Matched: Recent (24h)")
        await show_recent_transactions_for_message(message, state, api_client, storage)
    elif text == "📅 By Date" or text == button_by_date:
        logger.info(f"✅ Matched: By Date")
        await request_date_for_message(message, state, templates, lang)
    elif text == "🌐 Open in Browser" or text == button_open_browser:
        logger.info(f"✅ Matched: Open in Browser")
        from app.utils.keyboards import get_browser_url
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        web_url = get_browser_url(player_uuid=None, user_role="admin")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_open_browser, url=web_url)]
        ])
        web_app_msg = await templates.get_template("web_app_description", lang, "🌐 Web App\n\nClick the button below to open the web app in your browser:")
        await message.answer(web_app_msg, reply_markup=keyboard)
    elif text == "🚪 Logout" or text == button_logout:
        logger.info(f"✅ Matched: Logout")
        await state.clear()
        await storage.clear_user_credentials(telegram_id)
        await storage.clear_admin_token(telegram_id)
        logout_msg = await templates.get_template("logout_success", lang, "✅ Logged out successfully!")
        await message.answer(logout_msg)
        from app.handlers.start import cmd_start
        await cmd_start(message, state, api_client, storage)


async def request_date_for_message(message: Message, state: FSMContext, templates: TextTemplates = None, lang: str = "en"):
    """Request date for filtering transactions (from text message)."""
    if templates is None:
        from app.utils.text_templates import TextTemplates
        from app.services.api_client import APIClient
        from app.storage import StorageInterface
        # This shouldn't happen, but provide fallback
        templates = TextTemplates(None, None)
        lang = "en"
    
    await state.set_state(AdminTransactionStates.entering_date)
    button_back = await templates.get_template("button_back", lang, "🔙 Back")
    filter_msg = await templates.get_template("admin_filter_by_date", lang, "📅 Filter by Date\n\nPlease enter the date (YYYY-MM-DD):\nExample: 2025-11-08")
    await message.answer(
        filter_msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_back, callback_data="admin:back")]
        ])
    )


@router.callback_query(F.data == "admin:logout")
async def admin_logout(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Admin logout from callback."""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    
    try:
        # Get access token
        access_token = await storage.get_admin_token(telegram_id)
        if access_token:
            # Call logout API
            try:
                await api_client.logout()
            except:
                pass  # Ignore logout API errors
        
        # Clear admin token and credentials
        await storage.clear_admin_token(telegram_id)
        await storage.clear_user_credentials(telegram_id)
        
        await callback.message.edit_text("✅ Logged out successfully.")
        await state.clear()
        
        # Return to start
        from app.handlers.start import cmd_start
        await cmd_start(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error during admin logout: {e}")
        await callback.message.edit_text("❌ Error during logout. Please try again.")


async def show_all_transactions_for_message(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show all transactions (shared function for message and callback)."""
    telegram_id = message.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Admin session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching transactions...")
        
        response = await api_client.get_admin_transactions(
            access_token=access_token,
            page=1,
            limit=20,
        )
        
        transactions = response.get("transactions", [])
        pagination = response.get("pagination", {})
        
        await processing_msg.delete()
        
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        
        if not transactions:
            all_tx_button = await templates.get_template("button_all_transactions", lang, "📋 All Transactions")
            empty_msg = await templates.get_template("history_empty", lang, "No transactions found.")
            await message.answer(
                f"{all_tx_button}\n\n{empty_msg}",
                reply_markup=build_admin_back_keyboard()
            )
            return
        
        # Store transactions in state for later use
        transactions_dict = {tx.get("id"): tx for tx in transactions}
        await state.update_data(transactions_cache=transactions_dict)
        
        # Build transaction list
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        all_tx_button = await templates.get_template("button_all_transactions", lang, "📋 All Transactions")
        text = f"{all_tx_button}\n\n"
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
                callback_data=f"admin:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin:back")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching all transactions: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching transactions.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data == "admin:transactions:all")
async def show_all_transactions(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show all transactions (callback handler)."""
    await callback.answer()
    await show_all_transactions_for_message(callback.message, state, api_client, storage)


async def show_recent_transactions_for_message(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show recent transactions (last 24 hours) - shared function for message and callback."""
    telegram_id = message.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Admin session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching recent transactions...")
        
        # Calculate datetime 24 hours ago (not just date)
        from datetime import timezone
        now = datetime.now(timezone.utc)  # Use UTC for consistent comparison
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Note: API might not support date filtering directly, so we'll fetch all and filter client-side
        # Or use the API if it supports date filtering
        response = await api_client.get_admin_transactions(
            access_token=access_token,
            page=1,
            limit=100,  # Get more transactions to filter
        )
        
        transactions = response.get("transactions", [])
        
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
                reply_markup=build_admin_back_keyboard()
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
                callback_data=f"admin:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin:back")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}", exc_info=True)
        await message.answer(
            f"❌ Error fetching recent transactions.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data == "admin:transactions:recent")
async def show_recent_transactions(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show recent transactions (callback handler)."""
    await callback.answer()
    await show_recent_transactions_for_message(callback.message, state, api_client, storage)


@router.callback_query(F.data == "admin:transactions:date")
async def request_date(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Request date for filtering transactions."""
    await callback.answer()
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(callback.from_user.id)
    button_back = await templates.get_template("button_back", lang, "🔙 Back")
    filter_msg = await templates.get_template("admin_filter_by_date", lang, "📅 Filter by Date\n\nPlease enter the date (YYYY-MM-DD):\nExample: 2025-11-08")
    
    await state.set_state(AdminTransactionStates.entering_date)
    await callback.message.edit_text(
        filter_msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_back, callback_data="admin:back")]
        ])
    )


@router.message(AdminTransactionStates.entering_date, F.text)
async def show_transactions_by_date(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transactions for a specific date."""
    date_str = message.text.strip()
    
    try:
        # Validate date format
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_obj.strftime("%Y-%m-%d")
        end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    except ValueError:
        # Check if it's a menu command instead of a date
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(message.from_user.id)
        
        button_all_tx = await templates.get_template("button_all_transactions", lang, "📋 All Transactions")
        button_recent = await templates.get_template("button_recent_24h", lang, "🕐 Recent (24h)")
        button_by_date = await templates.get_template("button_by_date", lang, "📅 By Date")
        button_open_browser = await templates.get_template("button_open_browser", lang, "🌐 Open in Browser")
        button_logout = await templates.get_template("button_logout", lang, "🚪 Logout")
        button_back = await templates.get_template("button_back", lang, "🔙 Back")
        
        # Check common buttons and potential localized versions
        is_menu_command = (
            date_str in [button_all_tx, button_recent, button_by_date, button_open_browser, button_logout, button_back] or
            date_str.startswith(("📋", "🕐", "📅", "🌐", "🚪", "🔙", "📱"))
        )
        
        if is_menu_command:
            logger.info(f"🔄 User sent menu command '{date_str}' while in date input mode. Switching context.")
            await state.clear()
            await handle_admin_menu_buttons(message, state, api_client, storage)
            return

        await message.answer(
            "❌ Invalid date format. Please use YYYY-MM-DD format.\n"
            "Example: 2025-11-08"
        )
        return
    
    telegram_id = message.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await message.answer("❌ Admin session expired. Please login again.")
        return
    
    try:
        processing_msg = await message.answer("⏳ Fetching transactions...")
        
        # Use server-side filtering
        response = await api_client.get_admin_transactions(
            access_token=access_token,
            page=1,
            limit=50,
            date_range=f"{start_date},{end_date}"
        )
        
        filtered_transactions = response.get("transactions", [])
        
        await processing_msg.delete()
        
        if not filtered_transactions:
            await message.answer(
                f"📅 Transactions for {start_date}\n\n"
                "No transactions found for this date.",
                reply_markup=build_admin_back_keyboard()
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
                callback_data=f"admin:tx:{tx_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin:back")])
        
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


@router.callback_query(F.data.startswith("admin:tx:"))
async def show_transaction_details(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transaction details with action buttons."""
    await callback.answer()
    
    transaction_id = int(callback.data.split(":")[-1])
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Admin session expired. Please login again.")
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
            response = await api_client.get_admin_transactions(
                access_token=access_token,
                page=1,
                limit=100,  # Get more to find the transaction
            )
            
            transactions = response.get("transactions", [])
            
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
        
        # Log transaction structure for debugging
        logger.info(f"📋 Transaction data for ID {transaction_id}: {tx}")
        logger.debug(f"📋 Transaction keys: {list(tx.keys()) if isinstance(tx, dict) else 'Not a dict'}")
        
        # Format transaction details with fallbacks for different field names
        tx_type = tx.get("type") or tx.get("transactionType") or "N/A"
        tx_status = tx.get("status") or "N/A"
        
        # Handle amount (could be string, int, or float)
        tx_amount_raw = tx.get("amount")
        if tx_amount_raw is None:
            tx_amount = "N/A"
        elif isinstance(tx_amount_raw, (int, float)):
            tx_amount = f"{tx_amount_raw:.2f}".rstrip('0').rstrip('.')
        else:
            tx_amount = str(tx_amount_raw)
        
        tx_currency = tx.get("currency") or "ETB"
        tx_uuid = tx.get("transactionUuid") or tx.get("uuid") or tx.get("id") or "N/A"
        
        # Handle date (try multiple field names)
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
        assigned_agent = tx.get("assignedAgent") or tx.get("assigned_agent") or {}
        
        # Additional fields
        withdrawal_address = tx.get("withdrawalAddress") or tx.get("withdrawal_address")
        player_site_id = tx.get("playerSiteId") or tx.get("player_site_id")
        screenshot_url = tx.get("screenshotUrl") or tx.get("screenshot_url")
        
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
        if assigned_agent:
            agent_name = assigned_agent.get("displayName") or assigned_agent.get("display_name") or assigned_agent.get("username") or "N/A"
            text += f"Assigned Agent: {agent_name}\n"
        if screenshot_url:
            # Make screenshot URL clickable
            text += f"\n📎 Screenshot: <a href=\"{screenshot_url}\">View Image</a>\n"
        
        # Store transaction ID in state
        await state.update_data(selected_transaction_id=transaction_id)
        
        # Build action buttons
        buttons = [
            [InlineKeyboardButton(text="👤 Assign Agent", callback_data=f"admin:assign:{transaction_id}")],
            [InlineKeyboardButton(text="✅ Update Status", callback_data=f"admin:status:{transaction_id}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin:back")]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Send transaction details with screenshot as image if available
        if screenshot_url:
            try:
                # Try to send the screenshot as an image
                from aiogram.types import URLInputFile
                try:
                    await callback.message.delete()  # Try to delete the previous message
                except:
                    pass  # Ignore if deletion fails (message might be too old)
                
                await callback.message.answer_photo(
                    photo=URLInputFile(screenshot_url),
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not send screenshot as image: {e}, sending as text with link")
                # Fallback: send as text with clickable link
                try:
                    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
                except:
                    # If edit fails, send new message
                    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing transaction details: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error loading transaction details.\n\n"
            f"Error: {type(e).__name__}"
        )


@router.callback_query(F.data.startswith("admin:assign:"))
async def assign_agent_start(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Start agent assignment process."""
    await callback.answer()
    
    transaction_id = int(callback.data.split(":")[-1])
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Admin session expired. Please login again.")
        return
    
    try:
        # Get agents list
        processing_msg = await callback.message.answer("⏳ Loading agents...")
        
        agents_response = await api_client.get_agents(access_token)
        agents = agents_response.get("agents", [])
        
        await processing_msg.delete()
        
        if not agents:
            await callback.message.edit_text(
                "❌ No agents available.",
                reply_markup=build_admin_back_keyboard()
            )
            return
        
        # Store transaction ID
        await state.update_data(selected_transaction_id=transaction_id)
        await state.set_state(AdminTransactionStates.assigning_agent)
        
        # Build agent selection buttons
        buttons = []
        for agent in agents:
            agent_id = agent.get("id")
            agent_name = agent.get("displayName", agent.get("username", "Unknown"))
            buttons.append([InlineKeyboardButton(
                text=f"👤 {agent_name}",
                callback_data=f"admin:assign_agent:{transaction_id}:{agent_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Cancel", callback_data=f"admin:tx:{transaction_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(
            f"👤 Assign Agent\n\n"
            f"Transaction ID: {transaction_id}\n\n"
            f"Select an agent:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error loading agents: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error loading agents.\n\n"
            f"Error: {type(e).__name__}"
        )


@router.callback_query(F.data.startswith("admin:assign_agent:"))
async def assign_agent_confirm(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Confirm and assign agent to transaction."""
    await callback.answer()
    
    parts = callback.data.split(":")
    transaction_id = int(parts[2])
    agent_id = int(parts[3])
    
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Admin session expired. Please login again.")
        return
    
    try:
        processing_msg = await callback.message.answer("⏳ Assigning agent...")
        
        response = await api_client.assign_transaction_to_agent(
            access_token=access_token,
            transaction_id=transaction_id,
            agent_id=agent_id,
        )
        
        await processing_msg.delete()
        
        updated_transaction = response.get("transaction", {})
        agent_name = updated_transaction.get("assignedAgent", {}).get("displayName", "Unknown")
        
        # Update cache with updated transaction
        data = await state.get_data()
        transactions_cache = data.get("transactions_cache", {})
        transactions_cache[transaction_id] = updated_transaction
        await state.update_data(transactions_cache=transactions_cache)
        logger.info(f"✅ Updated transaction {transaction_id} in cache after agent assignment")
        
        await callback.message.edit_text(
            f"✅ Agent Assigned Successfully!\n\n"
            f"Transaction ID: {transaction_id}\n"
            f"Agent: {agent_name}\n\n"
            f"Transaction has been assigned to the agent.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to Transaction", callback_data=f"admin:tx:{transaction_id}")],
                [InlineKeyboardButton(text="🏠 Admin Menu", callback_data="admin:back")]
            ])
        )
        # Clear state to allow other actions (like Reply Keyboard) to work
        await state.set_state(None)
        
    except Exception as e:
        logger.error(f"Error assigning agent: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error assigning agent.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data.startswith("admin:status:"))
async def update_status_start(callback: CallbackQuery, state: FSMContext):
    """Start status update process."""
    await callback.answer()
    
    transaction_id = int(callback.data.split(":")[-1])
    
    # Store transaction ID
    await state.update_data(selected_transaction_id=transaction_id)
    await state.set_state(AdminTransactionStates.updating_status)
    
    # Status options
    buttons = [
        [InlineKeyboardButton(text="⏳ PENDING", callback_data=f"admin:set_status:{transaction_id}:PENDING")],
        [InlineKeyboardButton(text="🔄 IN_PROGRESS", callback_data=f"admin:set_status:{transaction_id}:IN_PROGRESS")],
        [InlineKeyboardButton(text="✅ SUCCESS", callback_data=f"admin:set_status:{transaction_id}:SUCCESS")],
        [InlineKeyboardButton(text="❌ FAILED", callback_data=f"admin:set_status:{transaction_id}:FAILED")],
        [InlineKeyboardButton(text="🚫 CANCELLED", callback_data=f"admin:set_status:{transaction_id}:CANCELLED")],
        [InlineKeyboardButton(text="🔙 Cancel", callback_data=f"admin:tx:{transaction_id}")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"✅ Update Status\n\n"
        f"Transaction ID: {transaction_id}\n\n"
        f"Select new status:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("admin:set_status:"))
async def update_status_confirm(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Confirm and update transaction status."""
    await callback.answer()
    
    parts = callback.data.split(":")
    transaction_id = int(parts[2])
    status = parts[3]
    
    telegram_id = callback.from_user.id
    access_token = await storage.get_admin_token(telegram_id)
    
    if not access_token:
        await callback.message.edit_text("❌ Admin session expired. Please login again.")
        return
    
    try:
        processing_msg = await callback.message.answer("⏳ Updating status...")
        
        response = await api_client.update_transaction_status(
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
        transactions_cache[transaction_id] = updated_transaction
        await state.update_data(transactions_cache=transactions_cache)
        logger.info(f"✅ Updated transaction {transaction_id} in cache after status update")
        
        await callback.message.edit_text(
            f"✅ Status Updated Successfully!\n\n"
            f"Transaction ID: {transaction_id}\n"
            f"New Status: {new_status}\n\n"
            f"Transaction status has been updated.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to Transaction", callback_data=f"admin:tx:{transaction_id}")],
                [InlineKeyboardButton(text="🏠 Admin Menu", callback_data="admin:back")]
            ])
        )
        # Clear state to allow other actions (like Reply Keyboard) to work
        await state.set_state(None)
        
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Error updating status.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try again."
        )


@router.callback_query(F.data == "admin:back")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Go back to admin menu."""
    await callback.answer()
    # Don't clear state completely - preserve transactions_cache if it exists
    # Only clear FSM states, not the cache
    current_data = await state.get_data()
    transactions_cache = current_data.get("transactions_cache", {})
    
    # Clear state but preserve cache
    await state.clear()
    if transactions_cache:
        await state.update_data(transactions_cache=transactions_cache)
    
    await show_admin_menu(callback.message, state, api_client, storage)


def build_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Build back to admin menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Admin Menu", callback_data="admin:back")]
    ])

