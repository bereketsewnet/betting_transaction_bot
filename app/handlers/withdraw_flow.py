"""Withdraw flow handler with FSM."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pathlib import Path
import logging
from typing import Dict, Any

from app.services.api_client import APIClient
from app.services.player_service import PlayerService
from app.services.file_service import FileService
from app.utils.keyboards import (
    build_paginated_inline_keyboard,
    build_amount_quick_replies,
    build_confirmation_keyboard,
    build_back_keyboard,
)
from app.utils.validators import validate_amount, validate_player_site_id
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface

logger = logging.getLogger(__name__)

router = Router()


class WithdrawStates(StatesGroup):
    """FSM states for withdraw flow."""
    selecting_bank = State()
    entering_required_fields = State()
    entering_amount = State()
    selecting_betting_site = State()
    entering_player_site_id = State()
    uploading_screenshot = State()
    confirming = State()


async def start_withdraw_flow(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Start withdraw flow."""
    try:
        # Get withdrawal banks
        logger.info(f"🔄 Fetching withdrawal banks for user {message.from_user.id}")
        banks = await api_client.get_withdrawal_banks()
        logger.info(f"📊 Received {len(banks)} withdrawal banks from API")
        
        active_banks = [bank for bank in banks if bank.isActive]
        logger.info(f"✅ Found {len(active_banks)} active withdrawal banks")
        
        # If no active banks but we have banks, show all banks
        if not active_banks and banks:
            logger.warning(f"⚠️ No active banks found, but {len(banks)} total banks. Showing all banks.")
            active_banks = banks
        
        if not active_banks:
            logger.error(f"❌ No withdrawal banks available for user {message.from_user.id}")
            await message.answer("❌ No withdrawal banks available. Please contact support.")
            return
        
        # Build paginated bank list
        buttons = [(bank.bankName, f"bank:withdraw:{bank.id}") for bank in active_banks]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="bank:withdraw")
        
        await state.set_state(WithdrawStates.selecting_bank)
        await message.answer(
            "💸 Withdraw\n\nSelect a withdrawal bank:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error starting withdraw flow: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.callback_query(F.data.startswith("bank:withdraw:"), WithdrawStates.selecting_bank)
async def select_withdraw_bank(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle withdrawal bank selection."""
    await callback.answer()
    
    bank_id = int(callback.data.split(":")[-1])
    
    try:
        # Get bank details
        banks = await api_client.get_withdrawal_banks()
        bank = next((b for b in banks if b.id == bank_id), None)
        
        if not bank:
            await callback.message.edit_text("❌ Bank not found.")
            return
        
        # Store bank selection
        await state.update_data(withdrawal_bank_id=bank_id, bank=bank.dict())
        
        # Check required fields
        required_fields = bank.requiredFields if bank.requiredFields else []
        
        if required_fields:
            # Store required fields and start collecting them
            await state.update_data(
                required_fields=required_fields,
                current_field_index=0,
                withdrawal_fields={}
            )
            await state.set_state(WithdrawStates.entering_required_fields)
            
            # Ask for first field
            field = required_fields[0]
            await callback.message.edit_text(
                f"🏦 {bank.bankName}\n\n"
                f"Please enter {field.label}:",
                reply_markup=build_back_keyboard()
            )
        else:
            # No required fields, proceed to amount
            await proceed_to_amount(callback.message, state)
            
    except Exception as e:
        logger.error(f"Error selecting withdraw bank: {e}")
        await callback.message.edit_text("❌ An error occurred. Please try again.")


@router.message(WithdrawStates.entering_required_fields, F.text)
async def process_required_field(message: Message, state: FSMContext):
    """Process required field input."""
    data = await state.get_data()
    required_fields = data["required_fields"]
    current_index = data["current_field_index"]
    withdrawal_fields = data.get("withdrawal_fields", {})
    
    field = required_fields[current_index]
    field_value = message.text.strip()
    
    if field.required and not field_value:
        await message.answer(f"❌ {field.label} is required. Please enter a value:")
        return
    
    # Store field value
    withdrawal_fields[field.name] = field_value
    await state.update_data(withdrawal_fields=withdrawal_fields)
    
    # Move to next field
    next_index = current_index + 1
    
    if next_index < len(required_fields):
        # Ask for next field
        next_field = required_fields[next_index]
        await state.update_data(current_field_index=next_index)
        await message.answer(f"Please enter {next_field.label}:")
    else:
        # All fields collected, proceed to amount
        await state.update_data(withdrawal_address=", ".join(withdrawal_fields.values()))
        await proceed_to_amount(message, state)


async def proceed_to_amount(message: Message, state: FSMContext):
    """Proceed to amount selection."""
    keyboard = build_amount_quick_replies()
    await state.set_state(WithdrawStates.entering_amount)
    await message.answer(
        "Enter the withdrawal amount:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("amount:"), WithdrawStates.entering_amount)
async def select_withdraw_amount(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle amount selection."""
    await callback.answer()
    
    amount_data = callback.data.split(":", 1)[1]
    
    if amount_data == "custom":
        await state.set_state(WithdrawStates.entering_amount)
        await callback.message.edit_text(
            "Enter custom amount (e.g., 150.50):",
            reply_markup=build_back_keyboard()
        )
    else:
        try:
            amount = float(amount_data)
            await state.update_data(amount=amount)
            await proceed_to_betting_site(callback.message, state, api_client)
        except ValueError:
            await callback.message.edit_text("❌ Invalid amount. Please try again.")


@router.message(WithdrawStates.entering_amount, F.text)
async def process_withdraw_amount(message: Message, state: FSMContext, api_client: APIClient):
    """Process custom amount input."""
    is_valid, amount, error = validate_amount(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Please try again:")
        return
    
    await state.update_data(amount=amount)
    await proceed_to_betting_site(message, state, api_client)


async def proceed_to_betting_site(message: Message, state: FSMContext, api_client: APIClient):
    """Proceed to betting site selection."""
    try:
        betting_sites = await api_client.get_betting_sites(is_active=True)
        
        if not betting_sites:
            await message.answer("❌ No betting sites available.")
            return
        
        buttons = [(site.name, f"site:withdraw:{site.id}") for site in betting_sites]
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="site:withdraw")
        
        await state.set_state(WithdrawStates.selecting_betting_site)
        await message.answer(
            "Select a betting site:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error getting betting sites: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.callback_query(F.data.startswith("site:withdraw:"), WithdrawStates.selecting_betting_site)
async def select_withdraw_betting_site(callback: CallbackQuery, state: FSMContext):
    """Handle betting site selection."""
    await callback.answer()
    
    site_id = int(callback.data.split(":")[-1])
    await state.update_data(betting_site_id=site_id)
    await state.set_state(WithdrawStates.entering_player_site_id)
    
    await callback.message.edit_text(
        "Enter your Player Site ID (your username/ID on the betting site):",
        reply_markup=build_back_keyboard()
    )


@router.message(WithdrawStates.entering_player_site_id, F.text)
async def process_withdraw_player_site_id(message: Message, state: FSMContext):
    """Process player site ID input."""
    is_valid, error = validate_player_site_id(message.text)
    
    if not is_valid:
        await message.answer(f"❌ {error}. Please try again:")
        return
    
    await state.update_data(player_site_id=message.text.strip())
    await state.set_state(WithdrawStates.uploading_screenshot)
    
    await message.answer(
        "📸 Upload a screenshot (optional):\n\n"
        "Send a photo or type /skip to continue without screenshot."
    )


@router.message(WithdrawStates.uploading_screenshot, F.photo)
async def process_withdraw_screenshot(message: Message, state: FSMContext):
    """Process screenshot upload."""
    photo: PhotoSize = message.photo[-1]
    await state.update_data(screenshot_file_id=photo.file_id)
    await proceed_to_withdraw_confirmation(message, state)


@router.message(WithdrawStates.uploading_screenshot, F.text == "/skip")
async def skip_withdraw_screenshot(message: Message, state: FSMContext):
    """Skip screenshot upload."""
    await state.update_data(screenshot_file_id=None)
    await proceed_to_withdraw_confirmation(message, state)


async def proceed_to_withdraw_confirmation(message: Message, state: FSMContext):
    """Proceed to confirmation step."""
    data = await state.get_data()
    
    summary = f"""
📋 Transaction Summary

Type: WITHDRAW
Amount: ETB {data.get('amount', 0):.2f}
Bank ID: {data.get('withdrawal_bank_id')}
Withdrawal Address: {data.get('withdrawal_address', 'N/A')}
Betting Site ID: {data.get('betting_site_id')}
Player Site ID: {data.get('player_site_id')}
Screenshot: {'Yes' if data.get('screenshot_file_id') else 'No'}

Please confirm to proceed:
    """
    
    keyboard = build_confirmation_keyboard()
    await state.set_state(WithdrawStates.confirming)
    await message.answer(summary, reply_markup=keyboard)


@router.callback_query(F.data == "confirm:yes", WithdrawStates.confirming)
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext, bot, api_client: APIClient, storage: StorageInterface):
    """Confirm and create withdrawal transaction."""
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
            transaction_type="WITHDRAW",
            amount=data["amount"],
            currency="ETB",
            betting_site_id=data["betting_site_id"],
            player_site_id=data["player_site_id"],
            withdrawal_bank_id=data["withdrawal_bank_id"],
            withdrawal_address=data.get("withdrawal_address", ""),
            screenshot_path=screenshot_path,
        )
        
        # Cleanup screenshot
        if screenshot_path:
            await file_service.cleanup_file(screenshot_path)
        
        # Show success message
        await callback.message.edit_text(
            f"✅ Withdrawal transaction created successfully!\n\n"
            f"Transaction UUID: {transaction.transaction.transactionUuid}\n"
            f"Status: {transaction.transaction.status}\n\n"
            f"You will be notified when the transaction is processed."
        )
        
        await state.clear()
        
        # Show main menu after delay
        from asyncio import sleep
        await sleep(2)
        from app.handlers.main_menu import show_main_menu
        await show_main_menu(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"Error creating withdrawal: {e}")
        await callback.message.edit_text(
            f"❌ Failed to create withdrawal transaction.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again or contact support."
        )


@router.callback_query(F.data == "confirm:no", WithdrawStates.confirming)
async def cancel_withdraw(callback: CallbackQuery, state: FSMContext):
    """Cancel withdrawal transaction."""
    await callback.answer("Cancelled")
    await state.clear()
    await callback.message.edit_text("❌ Withdrawal transaction cancelled.")

