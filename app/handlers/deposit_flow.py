"""Deposit flow handler with FSM."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pathlib import Path
import logging

from app.services.api_client import APIClient
from app.services.player_service import PlayerService
from app.services.file_service import FileService
from app.utils.keyboards import (
    build_paginated_inline_keyboard,
    build_amount_quick_replies,
    build_confirmation_keyboard_async,
    build_back_keyboard,
)
from app.utils.validators import validate_amount, validate_player_site_id, validate_callback_data
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface
from app.handlers.inline_lists import handle_bank_selection, handle_betting_site_selection

logger = logging.getLogger(__name__)

router = Router()


class DepositStates(StatesGroup):
    """FSM states for deposit flow."""
    selecting_bank = State()
    entering_amount = State()
    selecting_betting_site = State()
    entering_player_site_id = State()
    uploading_screenshot = State()
    confirming = State()


async def start_deposit_flow(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Start deposit flow."""
    try:
        # Get deposit banks
        logger.info(f"🔄 Fetching deposit banks for user {message.from_user.id}")
        banks = await api_client.get_deposit_banks()
        logger.info(f"📊 Received {len(banks)} deposit banks from API")
        
        # Filter to only show active banks (isActive = true)
        active_banks = [bank for bank in banks if bank.isActive]
        logger.info(f"✅ Found {len(active_banks)} active deposit banks (filtered from {len(banks)} total)")
        
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(message.from_user.id)
        
        if not active_banks:
            logger.error(f"❌ No deposit banks available for user {message.from_user.id}")
            error_msg = await templates.get_template("error_no_deposit_banks", lang, "❌ No deposit banks available. Please contact support.")
            await message.answer(error_msg)
            return
        
        # Build paginated bank list
        buttons = [(bank.bankName, f"bank:deposit:{bank.id}") for bank in active_banks]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="bank:deposit")
        
        await state.set_state(DepositStates.selecting_bank)
        deposit_title = await templates.get_template("deposit_title", lang, "💵 Deposit\n\nSelect a deposit bank:")
        await message.answer(deposit_title, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error starting deposit flow: {e}")
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(message.from_user.id)
        error_msg = await templates.get_template("error_generic", lang, "❌ An error occurred. Please try again.")
        await message.answer(error_msg)


@router.callback_query(F.data.startswith("bank:deposit:"), DepositStates.selecting_bank)
async def select_deposit_bank(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle deposit bank selection."""
    await callback.answer()
    
    bank_id = int(callback.data.split(":")[-1])
    
    try:
        # Get bank details
        banks = await api_client.get_deposit_banks()
        bank = next((b for b in banks if b.id == bank_id), None)
        
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(callback.from_user.id)
        
        if not bank:
            error_msg = await templates.get_template("error_bank_not_found", lang, "❌ Bank not found.")
            await callback.message.edit_text(error_msg)
            return
        
        # Store bank selection
        await state.update_data(deposit_bank_id=bank_id, bank=bank.dict())
        
        # Show bank details and amount selection
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(callback.from_user.id)
        bank_details = templates.format_bank_details(bank.dict())
        
        keyboard = build_amount_quick_replies()
        await state.set_state(DepositStates.entering_amount)
        amount_msg = await templates.get_template("deposit_enter_amount", lang, "Enter the deposit amount:")
        await callback.message.edit_text(
            f"{bank_details}\n\n{amount_msg}",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error selecting deposit bank: {e}")
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(callback.from_user.id)
        error_msg = await templates.get_template("error_generic", lang, "❌ An error occurred. Please try again.")
        await callback.message.edit_text(error_msg)


@router.callback_query(F.data.startswith("amount:"), DepositStates.entering_amount)
async def select_amount(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle amount selection."""
    await callback.answer()
    
    amount_data = callback.data.split(":", 1)[1]
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(callback.from_user.id)
    
    if amount_data == "custom":
        # Get bank details from state to show them again
        data = await state.get_data()
        bank = data.get("bank", {})
        
        # Format bank details
        bank_details = templates.format_bank_details(bank)
        
        await state.set_state(DepositStates.entering_amount)
        amount_msg = await templates.get_template("deposit_enter_amount", lang, "Enter custom amount (e.g., 150.50):")
        await callback.message.edit_text(
            f"{bank_details}\n\n{amount_msg}",
            reply_markup=build_back_keyboard()
        )
    else:
        try:
            amount = float(amount_data)
            await state.update_data(amount=amount)
            await proceed_to_betting_site(callback.message, state, api_client, storage)
        except ValueError:
            error_msg = await templates.get_template("error_invalid_amount", lang, "❌ Invalid amount. Please try again.")
            await callback.message.edit_text(error_msg)


@router.message(DepositStates.entering_amount, F.text)
async def process_amount(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process custom amount input."""
    # Get bank details from state to show them
    data = await state.get_data()
    bank = data.get("bank", {})
    
    # Format bank details
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    bank_details = templates.format_bank_details(bank)
    
    is_valid, amount, error = validate_amount(message.text)
    
    if not is_valid:
        error_msg = await templates.get_template("error_invalid_amount", lang, f"❌ {error}. Please try again:")
        await message.answer(f"{bank_details}\n\n{error_msg}")
        return
    
    await state.update_data(amount=amount)
    await proceed_to_betting_site(message, state, api_client, storage)


async def proceed_to_betting_site(message_or_callback, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Proceed to betting site selection."""
    try:
        # Get amount from state
        data = await state.get_data()
        amount = data.get("amount", 0)
        
        templates = TextTemplates(api_client, storage)
        telegram_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
        lang = await templates.get_user_language(telegram_id)
        
        betting_sites = await api_client.get_betting_sites(is_active=True)
        
        if not betting_sites:
            error_msg = await templates.get_template("error_no_betting_sites", lang, "❌ No betting sites available.")
            await message_or_callback.answer(error_msg)
            return
        
        buttons = [(site.name, f"site:{site.id}") for site in betting_sites]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="site")
        
        await state.set_state(DepositStates.selecting_betting_site)
        
        site_msg = await templates.get_template("deposit_select_betting_site", lang, "Select a betting site:")
        message_text = f"✅ Amount: ETB {amount:.2f}\n\n{site_msg}"
        
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(message_text, reply_markup=keyboard)
        else:
            await message_or_callback.message.edit_text(message_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error getting betting sites: {e}")
        templates = TextTemplates(api_client, storage)
        telegram_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
        lang = await templates.get_user_language(telegram_id)
        error_msg = await templates.get_template("error_generic", lang, "❌ An error occurred. Please try again.")
        await message_or_callback.answer(error_msg)


@router.callback_query(F.data.startswith("site:"), DepositStates.selecting_betting_site)
async def select_betting_site(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle betting site selection."""
    await callback.answer()
    
    site_id = int(callback.data.split(":")[-1])
    await state.update_data(betting_site_id=site_id)
    await state.set_state(DepositStates.entering_player_site_id)
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(callback.from_user.id)
    player_id_msg = await templates.get_template("deposit_enter_player_site_id", lang, "Enter your Player Site ID (your username/ID on the betting site):")
    await callback.message.edit_text(player_id_msg, reply_markup=build_back_keyboard())


@router.message(DepositStates.entering_player_site_id, F.text)
async def process_player_site_id(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process player site ID input."""
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    
    is_valid, error = validate_player_site_id(message.text)
    
    if not is_valid:
        error_msg = await templates.get_template("error_invalid_player_site_id", lang, f"❌ {error}. Please try again:")
        await message.answer(error_msg)
        return
    
    await state.update_data(player_site_id=message.text.strip())
    await state.set_state(DepositStates.uploading_screenshot)
    
    screenshot_msg = await templates.get_template("deposit_upload_screenshot", lang, "📎 Add attachment (optional):\n\nSend a photo or type /skip to continue without attachment.")
    await message.answer(screenshot_msg)


@router.message(DepositStates.uploading_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Process screenshot upload."""
    # Photo will be downloaded in confirmation handler
    # For now, store file_id
    photo: PhotoSize = message.photo[-1]  # Get largest photo
    await state.update_data(screenshot_file_id=photo.file_id)
    await proceed_to_confirmation(message, state, api_client, storage)


@router.message(DepositStates.uploading_screenshot, F.text)
async def handle_screenshot_text(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Handle text input when photo is expected (including skip command)."""
    # Check if user wants to skip (accept /skip, skip, Skip, SKIP, etc.)
    if message.text and message.text.lower().strip().lstrip('/') == 'skip':
        logger.info(f"⏭️ User {message.from_user.id} skipping screenshot upload in deposit flow (text: '{message.text}')")
        await state.update_data(screenshot_file_id=None)
        await proceed_to_confirmation(message, state, api_client, storage)
        return
    
    # Not a skip command, ask for photo again
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    screenshot_msg = await templates.get_template("deposit_upload_screenshot", lang, "📎 Please send a photo attachment or type /skip to continue without attachment.")
    
    # Ensure the skip instruction is clear even if template doesn't have it (optional safety)
    if "/skip" not in screenshot_msg and "skip" not in screenshot_msg.lower():
         screenshot_msg += "\n\n(Type /skip to skip this step)"
         
    await message.answer(screenshot_msg)


async def proceed_to_confirmation(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Proceed to confirmation step."""
    data = await state.get_data()
    
    templates = TextTemplates(api_client, storage)
    lang = await templates.get_user_language(message.from_user.id)
    
    # Get names for ID-only fields
    bank_name = data.get('bank', {}).get('bankName', f"ID: {data.get('deposit_bank_id')}")
    
    # We need to fetch betting site name if not stored
    site_name = f"ID: {data.get('betting_site_id')}"
    if data.get('betting_site_id'):
        try:
            # Ideally we would cache this or store object in state, but for now fetch again or filter
            # Since we don't have a direct get_betting_site(id) that returns name easily without full list or another call
            # let's try to get it from active sites (likely cached by client or fast enough)
            sites = await api_client.get_betting_sites(is_active=True)
            site = next((s for s in sites if s.id == int(data.get('betting_site_id'))), None)
            if site:
                site_name = site.name
        except Exception as e:
            logger.warning(f"Failed to fetch site name for confirmation: {e}")

    confirm_template = await templates.get_template("deposit_confirm", lang, "Please confirm your deposit:\n\nAmount: {currency} {amount}\nBank: {bank_name}\nBetting Site: {site_name}\nPlayer ID: {player_site_id}")
    
    # Format the template with variables
    # Note: using locals() or explicit dict to match template placeholders
    formatted_text = confirm_template.format(
        currency="ETB",
        amount=f"{data.get('amount', 0):.2f}",
        bank_name=bank_name,
        site_name=site_name,
        player_site_id=data.get('player_site_id', 'N/A')
    )
    
    # Add screenshot status if needed (though template might not have it, we can append it or rely on template)
    # The user didn't ask for screenshot status in the template example, but the previous summary had it.
    # If the template doesn't cover everything, we might need to adjust.
    # User's example template: 
    # እባክዎ የክፍያ አስገባትዎን ያረጋግጡ:\n\nመጠን: {currency} {amount}\nባንክ: {bank_name}\nየውርርድ ጣቢያ: {site_name}\nየተጫዋች መለያ: {player_site_id}
    
    keyboard = await build_confirmation_keyboard_async(templates, lang)
    await state.set_state(DepositStates.confirming)
    await message.answer(formatted_text, reply_markup=keyboard)


@router.callback_query(F.data == "confirm:yes", DepositStates.confirming)
async def confirm_deposit(callback: CallbackQuery, state: FSMContext, bot, api_client: APIClient, storage: StorageInterface):
    """Confirm and create deposit transaction."""
    await callback.answer("Processing...")
    
    data = await state.get_data()
    telegram_id = callback.from_user.id
    
    try:
        # Get player UUID
        player_service = PlayerService(api_client, storage)
        player_uuid = await player_service.get_player_uuid(telegram_id)
        
        if not player_uuid:
            player_uuid = await player_service.get_or_create_guest_player(telegram_id)
        
        # Download screenshot if provided
        screenshot_path = None
        file_service = FileService(api_client)
        
        if data.get("screenshot_file_id"):
            try:
                screenshot_path = await file_service.download_telegram_file(
                    bot, data["screenshot_file_id"]
                )
            except Exception as e:
                logger.error(f"Error downloading screenshot: {e}")
                await callback.message.edit_text("❌ Failed to download screenshot. Please try again.")
                return
        
        # Create transaction
        transaction = await api_client.create_transaction(
            player_uuid=player_uuid,
            transaction_type="DEPOSIT",
            amount=data["amount"],
            currency="ETB",
            betting_site_id=data["betting_site_id"],
            player_site_id=data["player_site_id"],
            deposit_bank_id=data["deposit_bank_id"],
            screenshot_path=screenshot_path,
        )
        
        # Cleanup screenshot
        if screenshot_path:
            await file_service.cleanup_file(screenshot_path)
        
        # Show success message
        templates = TextTemplates(api_client, storage)
        lang = await templates.get_user_language(telegram_id)
        created_msg = await templates.get_template("transaction_created", lang, "✅ Your transaction has been created successfully!")
        processed_msg = await templates.get_template("transaction_processed", lang, "You will be notified when the transaction is processed.")
        
        # Format messages using format() method to replace all placeholders
        success_text = created_msg.format(
            transaction_uuid=transaction.transaction.transactionUuid,
            currency="ETB",
            amount=f"{data['amount']:.2f}",
            status=transaction.transaction.status
        )
        
        # Don't append English fallback text if template is used
        # success_text += f"\n\nTransaction UUID: {transaction.transaction.transactionUuid}\n"
        # success_text += f"Status: {transaction.transaction.status}\n\n"
        
        # Add processed message (usually empty initially for deposits, but keeping for structure)
        # Note: transaction_processed template usually has {transaction_uuid} and {status}
        # If the template is intended for a later update, we might not want to show it now unless it's part of the initial success flow.
        # Looking at the template content: '🎉 Your transaction has been processed!...' - This sounds like a completed state message.
        # The seed file has 'transaction_created' which says 'You can check the status in your transaction history.'
        # So 'transaction_processed' might be for updates.
        # However, the previous code appended it. Let's assume we only need 'transaction_created' for now.
        
        # Actually, let's check if we should append anything else.
        # The user complaint was about showing variables and mixed English.
        # So we should rely PURELY on the formatted template.
        
        await callback.message.edit_text(success_text)
        
        await state.clear()
        
        # Show main menu after delay
        from aiogram import Bot
        from asyncio import sleep
        await sleep(2)
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error creating deposit: {e}")
        await callback.message.edit_text(
            f"❌ Failed to create deposit transaction.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again or contact support."
        )


@router.callback_query(F.data == "confirm:no", DepositStates.confirming)
async def cancel_deposit(callback: CallbackQuery, state: FSMContext):
    """Cancel deposit transaction."""
    await callback.answer("Cancelled")
    await state.clear()
    await callback.message.edit_text("❌ Deposit transaction cancelled.")


@router.callback_query(F.data == "cancel")
async def cancel_flow(callback: CallbackQuery, state: FSMContext):
    """Cancel current flow."""
    await callback.answer("Cancelled")
    await state.clear()
    await callback.message.edit_text("❌ Cancelled.")

