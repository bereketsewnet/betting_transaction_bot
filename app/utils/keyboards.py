"""Keyboard builders for inline and reply keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional, Dict, Any


def build_inline_keyboard(
    buttons: List[tuple[str, str]],
    row_width: int = 2,
) -> InlineKeyboardMarkup:
    """Build inline keyboard from list of (text, callback_data) tuples."""
    keyboard = []
    row = []
    for text, callback_data in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if len(row) >= row_width:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_paginated_inline_keyboard(
    items: List[tuple[str, str]],
    page: int = 1,
    items_per_page: int = 6,
    callback_prefix: str = "item",
) -> tuple[InlineKeyboardMarkup, int]:
    """Build paginated inline keyboard.
    
    Returns:
        tuple: (keyboard, total_pages)
    """
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
    
    # Ensure page is within bounds
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    keyboard = []
    for text, callback_data in page_items:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    
    # Add navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀ Prev",
                callback_data=f"{callback_prefix}:page:{page-1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Next ▶",
                callback_data=f"{callback_prefix}:page:{page+1}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard), total_pages


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build main menu reply keyboard."""
    keyboard = [
        [KeyboardButton(text="💵 Deposit")],
        [KeyboardButton(text="💸 Withdraw")],
        [KeyboardButton(text="📜 History")],
        [KeyboardButton(text="🌐 Open Web App")],
        [KeyboardButton(text="ℹ️ Help")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_amount_quick_replies() -> InlineKeyboardMarkup:
    """Build quick amount selection buttons."""
    amounts = [50, 100, 200, 500, 1000, "Custom"]
    buttons = []
    row = []
    for amount in amounts:
        if amount == "Custom":
            row.append(InlineKeyboardButton(text="✏️ Custom", callback_data="amount:custom"))
        else:
            row.append(InlineKeyboardButton(text=f"${amount}", callback_data=f"amount:{amount}"))
        if len(row) >= 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Build confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="confirm:no"),
        ]
    ])


def build_back_keyboard(callback_data: str = "back:main") -> InlineKeyboardMarkup:
    """Build back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data=callback_data)]
    ])

