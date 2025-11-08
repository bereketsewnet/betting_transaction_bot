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
        
        # Store transactions in state for later use (avoid API call when showing details)
        transactions_dict = {tx.transactionUuid: tx.dict() for tx in transactions}
        await state.update_data(transactions_cache=transactions_dict)
        
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
        logger.error(f"❌ Error showing transaction history for user {telegram_id}: {e}", exc_info=True)
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error details: {str(e)[:200]}")
        
        error_msg = "❌ An error occurred while fetching transaction history."
        error_str = str(e).lower()
        
        if "telegramusername" in error_str or "must be a string" in error_str:
            error_msg += "\n\nPlease try again or contact support."
        elif "400" in error_str or "validation" in error_str:
            error_msg += "\n\nValidation error. Please contact support."
        elif "connection" in error_str or "timeout" in error_str:
            error_msg += "\n\nCannot connect to server. Please try again."
        else:
            error_msg += f"\n\nError: {type(e).__name__}"
        
        await message.answer(error_msg)


@router.callback_query(F.data.startswith("tx:"))
async def show_transaction_details(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Show transaction details using cached data."""
    await callback.answer()
    
    transaction_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Get cached transactions from state (already fetched in show_transaction_history)
        data = await state.get_data()
        transactions_cache = data.get("transactions_cache", {})
        
        if transaction_uuid in transactions_cache:
            # Use cached transaction data (no API call needed)
            logger.info(f"📋 Using cached transaction data for {transaction_uuid}")
            transaction_data = transactions_cache[transaction_uuid]
        else:
            # Fallback: if not in cache, fetch from API (shouldn't happen normally)
            logger.warning(f"⚠️ Transaction {transaction_uuid} not in cache, fetching from API")
            telegram_id = callback.from_user.id
            player_service = PlayerService(api_client, storage)
            player_uuid = await player_service.get_player_uuid(telegram_id)
            
            if not player_uuid:
                await callback.message.edit_text("❌ Player not found.")
                return
            
            transaction_response = await api_client.get_transaction(
                transaction_id=transaction_uuid,
                player_uuid=player_uuid,
            )
            transaction_data = transaction_response.transaction.dict()
        
        # Format transaction details
        templates = TextTemplates(api_client)
        details = templates.format_transaction_details(transaction_data)
        
        await callback.message.edit_text(
            details,
            reply_markup=build_back_keyboard("back:history")
        )
        
    except Exception as e:
        logger.error(f"Error showing transaction details: {e}")
        await callback.message.edit_text("❌ Failed to load transaction details.")


@router.callback_query(F.data == "back:history")
async def back_to_history(callback: CallbackQuery, state: FSMContext, api_client: APIClient, storage: StorageInterface):
    """Go back to transaction history using cached data."""
    await callback.answer()
    
    try:
        # Try to use cached transactions first
        data = await state.get_data()
        transactions_cache = data.get("transactions_cache", {})
        
        if transactions_cache:
            # Rebuild transaction list from cache
            logger.info(f"📋 Rebuilding history list from cache ({len(transactions_cache)} transactions)")
            buttons = []
            for tx_uuid, tx_data in transactions_cache.items():
                tx_type = "💵" if tx_data.get("type") == "DEPOSIT" else "💸"
                tx_date = tx_data.get("createdAt", "").split("T")[0] if tx_data.get("createdAt") else "N/A"
                button_text = f"{tx_type} {tx_data.get('currency', 'N/A')} {tx_data.get('amount', 'N/A')} - {tx_data.get('status', 'N/A')} ({tx_date})"
                buttons.append((button_text, f"tx:{tx_uuid}"))
            
            keyboard, _ = build_paginated_inline_keyboard(buttons, callback_prefix="tx")
            
            await callback.message.edit_text(
                f"📜 Transaction History\n\n"
                f"Found {len(transactions_cache)} transaction(s). Select one to view details:",
                reply_markup=keyboard
            )
            return
        
        # If no cache, fetch from API (fallback)
        logger.info(f"📋 No cache found, fetching history from API")
        await show_transaction_history(callback.message, state, api_client, storage)
        
    except Exception as e:
        logger.error(f"❌ Error going back to history: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Failed to load transaction history.\n\n"
            f"Error: {type(e).__name__}\n"
            f"Please try selecting History from the main menu again."
        )

