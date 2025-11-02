"""Inline list pagination handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from app.services.api_client import APIClient
from app.utils.keyboards import build_paginated_inline_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("bank:deposit:page:"))
async def paginate_deposit_banks(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle deposit bank pagination."""
    await callback.answer()
    
    try:
        page = int(callback.data.split(":")[-1])
        banks = await api_client.get_deposit_banks()
        active_banks = [bank for bank in banks if bank.isActive]
        
        buttons = [(bank.bankName, f"bank:deposit:{bank.id}") for bank in active_banks]
        keyboard, _ = build_paginated_inline_keyboard(buttons, page=page, callback_prefix="bank:deposit")
        
        await callback.message.edit_text(
            "💵 Deposit\n\nSelect a deposit bank:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error paginating deposit banks: {e}")
        await callback.answer("❌ An error occurred.")


@router.callback_query(F.data.startswith("bank:withdraw:page:"))
async def paginate_withdraw_banks(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle withdrawal bank pagination."""
    await callback.answer()
    
    try:
        page = int(callback.data.split(":")[-1])
        banks = await api_client.get_withdrawal_banks()
        active_banks = [bank for bank in banks if bank.isActive]
        
        buttons = [(bank.bankName, f"bank:withdraw:{bank.id}") for bank in active_banks]
        keyboard, _ = build_paginated_inline_keyboard(buttons, page=page, callback_prefix="bank:withdraw")
        
        await callback.message.edit_text(
            "💸 Withdraw\n\nSelect a withdrawal bank:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error paginating withdraw banks: {e}")
        await callback.answer("❌ An error occurred.")


@router.callback_query(F.data.startswith("site:page:"))
async def paginate_betting_sites(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle betting site pagination."""
    await callback.answer()
    
    try:
        page = int(callback.data.split(":")[-1])
        sites = await api_client.get_betting_sites(is_active=True)
        
        buttons = [(site.name, f"site:{site.id}") for site in sites]
        keyboard, _ = build_paginated_inline_keyboard(buttons, page=page, callback_prefix="site")
        
        await callback.message.edit_text(
            "Select a betting site:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error paginating betting sites: {e}")
        await callback.answer("❌ An error occurred.")


@router.callback_query(F.data.startswith("site:withdraw:page:"))
async def paginate_withdraw_betting_sites(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Handle betting site pagination for withdraw."""
    await callback.answer()
    
    try:
        page = int(callback.data.split(":")[-1])
        sites = await api_client.get_betting_sites(is_active=True)
        
        buttons = [(site.name, f"site:withdraw:{site.id}") for site in sites]
        keyboard, _ = build_paginated_inline_keyboard(buttons, page=page, callback_prefix="site:withdraw")
        
        await callback.message.edit_text(
            "Select a betting site:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error paginating betting sites: {e}")
        await callback.answer("❌ An error occurred.")


async def handle_bank_selection(callback: CallbackQuery, state: FSMContext):
    """Placeholder for bank selection handler."""
    pass


async def handle_betting_site_selection(callback: CallbackQuery, state: FSMContext):
    """Placeholder for betting site selection handler."""
    pass

