"""Transaction history handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Optional
import logging

from app.services.api_client import APIClient
from app.services.player_service import PlayerService
from app.utils.keyboards import build_paginated_inline_keyboard, build_back_keyboard
from app.utils.text_templates import TextTemplates
from app.storage import StorageInterface

logger = logging.getLogger(__name__)

router = Router()


async def show_transaction_history(message: Message, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transaction history."""
    telegram_id = message.from_user.id
    
    try:
        # Get player UUID
        player_service = PlayerService(api_client, storage)
        player_uuid = await player_service.get_player_uuid(telegram_id)
        
        if not player_uuid:
            player_uuid = await player_service.get_or_create_guest_player(telegram_id)
        
        # Get transactions
        transactions_response = await api_client.get_transactions(
            player_uuid=player_uuid,
            page=1,
            limit=10,
        )
        
        transactions = transactions_response.transactions
        
        if not transactions:
            await message.answer(
                "📜 Transaction History\n\n"
                "No transactions found."
            )
            return
        
        # Build transaction list buttons
        buttons = []
        for tx in transactions:
            tx_type = "💵" if tx.type == "DEPOSIT" else "💸"
            tx_date = tx.createdAt.split("T")[0] if tx.createdAt else "N/A"
            button_text = f"{tx_type} {tx.currency} {tx.amount} - {tx.status} ({tx_date})"
            buttons.append((button_text, f"tx:{tx.transactionUuid}"))
        
        keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="tx")
        
        await message.answer(
            f"📜 Transaction History\n\n"
            f"Found {len(transactions)} transaction(s). Select one to view details:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing transaction history: {e}")
        await message.answer("❌ An error occurred while fetching transaction history.")


@router.callback_query(F.data.startswith("tx:"))
async def show_transaction_details(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transaction details."""
    await callback.answer()
    
    transaction_uuid = callback.data.split(":", 1)[1]
    telegram_id = callback.from_user.id
    
    try:
        # Get player UUID
        player_service = PlayerService(api_client, storage)
        player_uuid = await player_service.get_player_uuid(telegram_id)
        
        if not player_uuid:
            await callback.message.edit_text("❌ Player not found.")
            return
        
        # Get transaction details
        transaction_response = await api_client.get_transaction(
            transaction_id=transaction_uuid,
            player_uuid=player_uuid,
        )
        
        transaction = transaction_response.transaction
        
        # Format transaction details
        templates = TextTemplates(api_client)
        details = templates.format_transaction_details(transaction.dict())
        
        await callback.message.edit_text(
            details,
            reply_markup=build_back_keyboard("back:history")
        )
        
    except Exception as e:
        logger.error(f"Error showing transaction details: {e}")
        await callback.message.edit_text("❌ Failed to load transaction details.")


@router.callback_query(F.data == "back:history")
async def back_to_history(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Go back to transaction history."""
    await callback.answer()
    await show_transaction_history(callback.message, state, api_client, storage)

