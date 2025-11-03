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
    build_confirmation_keyboard,
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
        
        active_banks = [bank for bank in banks if bank.isActive]
        logger.info(f"✅ Found {len(active_banks)} active deposit banks")
        
        # If no active banks but we have banks, show all banks
        if not active_banks and banks:
            logger.warning(f"⚠️ No active banks found, but {len(banks)} total banks. Showing all banks.")
            active_banks = banks
        
        if not active_banks:
            logger.error(f"❌ No deposit banks available for user {message.from_user.id}")
            await message.answer("❌ No deposit banks available. Please contact support.")
            return
        
        # Build paginated bank list
        buttons = [(bank.bankName, f"bank:deposit:{bank.id}") for bank in active_banks]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="bank:deposit")
        
        await state.set_state(DepositStates.selecting_bank)
        await message.answer(
            "💵 Deposit\n\nSelect a deposit bank:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error starting deposit flow: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.callback_query(F.data.startswith("bank:deposit:"), DepositStates.selecting_bank)
async def select_deposit_bank(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle deposit bank selection."""
    await callback.answer()
    
    bank_id = int(callback.data.split(":")[-1])
    
    try:
        # Get bank details
        banks = await api_client.get_deposit_banks()
        bank = next((b for b in banks if b.id == bank_id), None)
        
        if not bank:
            await callback.message.edit_text("❌ Bank not found.")
            return
        
        # Store bank selection
        await state.update_data(deposit_bank_id=bank_id, bank=bank.dict())
        
        # Show bank details and amount selection
        templates = TextTemplates(api_client)
        bank_details = templates.format_bank_details(bank.dict())
        
        keyboard = build_amount_quick_replies()
        await state.set_state(DepositStates.entering_amount)
        await callback.message.edit_text(
            f"{bank_details}\n\n"
            f"Enter the deposit amount:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error selecting deposit bank: {e}")
        await callback.message.edit_text("❌ An error occurred. Please try again.")


@router.callback_query(F.data.startswith("amount:"), DepositStates.entering_amount)
async def select_amount(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle amount selection."""
    await callback.answer()
    
    amount_data = callback.data.split(":", 1)[1]
    
    if amount_data == "custom":
        # Get bank details from state to show them again
        data = await state.get_data()
        bank = data.get("bank", {})
        
        # Format bank details
        from app.utils.text_templates import TextTemplates
        templates = TextTemplates(api_client)
        bank_details = templates.format_bank_details(bank)
        
        await state.set_state(DepositStates.entering_amount)
        await callback.message.edit_text(
            f"{bank_details}\n\n"
            f"Enter custom amount (e.g., 150.50):",
            reply_markup=build_back_keyboard()
        )
    else:
        try:
            amount = float(amount_data)
            await state.update_data(amount=amount)
            await proceed_to_betting_site(callback.message, state, api_client)
        except ValueError:
            await callback.message.edit_text("❌ Invalid amount. Please try again.")


@router.message(DepositStates.entering_amount, F.text)
async def process_amount(message: Message, state: FSMContext, api_client: APIClient):
    """Process custom amount input."""
    # Get bank details from state to show them
    data = await state.get_data()
    bank = data.get("bank", {})
    
    # Format bank details
    from app.utils.text_templates import TextTemplates
    templates = TextTemplates(api_client)
    bank_details = templates.format_bank_details(bank)
    
    is_valid, amount, error = validate_amount(message.text)
    
    if not is_valid:
        await message.answer(
            f"{bank_details}\n\n"
            f"❌ {error}. Please try again:"
        )
        return
    
    await state.update_data(amount=amount)
    await proceed_to_betting_site(message, state, api_client)


async def proceed_to_betting_site(message_or_callback, state: FSMContext, api_client: APIClient):
    """Proceed to betting site selection."""
    try:
        # Get amount from state
        data = await state.get_data()
        amount = data.get("amount", 0)
        
        betting_sites = await api_client.get_betting_sites(is_active=True)
        
        if not betting_sites:
            await message_or_callback.answer("❌ No betting sites available.")
            return
        
        buttons = [(site.name, f"site:{site.id}") for site in betting_sites]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="site")
        
        await state.set_state(DepositStates.selecting_betting_site)
        
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(
                f"✅ Amount: ETB {amount:.2f}\n\n"
                f"Select a betting site:",
                reply_markup=keyboard
            )
        else:
            await message_or_callback.message.edit_text(
                f"✅ Amount: ETB {amount:.2f}\n\n"
                f"Select a betting site:",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error getting betting sites: {e}")
        await message_or_callback.answer("❌ An error occurred. Please try again.")


@router.callback_query(F.data.startswith("site:"), DepositStates.selecting_betting_site)
async def select_betting_site(callback: CallbackQuery, state: FSMContext):
    """Handle betting site selection."""
    await callback.answer()
    
    site_id = int(callback.data.split(":")[-1])
    await state.update_data(betting_site_id=site_id)
    await state.set_state(DepositStates.entering_player_site_id)
    
    await callback.message.edit_text(
        "Enter your Player Site ID (your username/ID on the betting site):",
        reply_markup=build_back_keyboard()
    )


@router.message(DepositStates.entering_player_site_id, F.text)
async def process_player_site_id(message: Message, state: FSMContext):
    """Process player site ID input."""
    is_valid, error = validate_player_site_id(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Please try again:")
        return
    
    await state.update_data(player_site_id=message.text.strip())
    await state.set_state(DepositStates.uploading_screenshot)
    
    await message.answer(
        "📸 Upload a screenshot of your payment (optional):\n\n"
        "Send a photo or type /skip to continue without screenshot."
    )


@router.message(DepositStates.uploading_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    """Process screenshot upload."""
    # Photo will be downloaded in confirmation handler
    # For now, store file_id
    photo: PhotoSize = message.photo[-1]  # Get largest photo
    await state.update_data(screenshot_file_id=photo.file_id)
    await proceed_to_confirmation(message, state)


@router.message(DepositStates.uploading_screenshot, F.text == "/skip")
async def skip_screenshot(message: Message, state: FSMContext):
    """Skip screenshot upload."""
    await state.update_data(screenshot_file_id=None)
    await proceed_to_confirmation(message, state)


async def proceed_to_confirmation(message: Message, state: FSMContext):
    """Proceed to confirmation step."""
    data = await state.get_data()
    
    summary = f"""
📋 Transaction Summary

Type: DEPOSIT
Amount: ETB {data.get('amount', 0):.2f}
Bank ID: {data.get('deposit_bank_id')}
Betting Site ID: {data.get('betting_site_id')}
Player Site ID: {data.get('player_site_id')}
Screenshot: {'Yes' if data.get('screenshot_file_id') else 'No'}

Please confirm to proceed:
    """
    
    keyboard = build_confirmation_keyboard()
    await state.set_state(DepositStates.confirming)
    await message.answer(summary, reply_markup=keyboard)


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
        await callback.message.edit_text(
            f"✅ Deposit transaction created successfully!\n\n"
            f"Transaction UUID: {transaction.transaction.transactionUuid}\n"
            f"Status: {transaction.transaction.status}\n\n"
            f"You will be notified when the transaction is processed."
        )
        
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

