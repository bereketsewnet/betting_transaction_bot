"""Keyboard builders for inline and reply keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import List, Optional, Dict, Any
from app.config import config


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


def get_web_app_url(player_uuid: Optional[str] = None) -> str:
    """Get web app URL with optional player UUID parameter (for mini app)."""
    # Use default if WEB_APP_URL is empty
    base_url = config.WEB_APP_URL.strip() if config.WEB_APP_URL else "https://websites.com"
    base_url = base_url.rstrip('/')
    if player_uuid:
        # Use path parameter: /player/{player_uuid}
        return f"{base_url}/player/{player_uuid}"
    return base_url


def get_browser_url(player_uuid: Optional[str] = None, user_role: Optional[str] = None) -> str:
    """Get web app URL for browser (all roles use base URL only).
    
    - All users (Player/Admin/Agent): WEB_APP_URL (base URL only, no player ID)
    """
    # Use default if WEB_APP_URL is empty
    base_url = config.WEB_APP_URL.strip() if config.WEB_APP_URL else "https://websites.com"
    base_url = base_url.rstrip('/')
    
    # All roles get base URL only (no player ID)
    return base_url


def is_https_url(url: str) -> bool:
    """Check if URL is HTTPS (required for Telegram Web Apps)."""
    return url.startswith('https://')


def is_valid_web_app_url(url: str) -> bool:
    """Check if URL is valid for Telegram Web Apps.
    
    Telegram Web Apps require:
    - HTTPS (not HTTP)
    - Not localhost (even with HTTPS, localhost is rejected)
    - Valid domain
    """
    if not url.startswith('https://'):
        return False
    
    # Telegram rejects localhost even with HTTPS
    if 'localhost' in url.lower() or '127.0.0.1' in url:
        return False
    
    return True


def build_main_menu_keyboard(show_logout: bool = False, player_uuid: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Build main menu reply keyboard with mini app button (if valid URL)."""
    web_app_url = get_web_app_url(player_uuid)
    
    # Check if URL is valid for Telegram Web Apps (HTTPS + not localhost)
    can_use_mini_app = is_valid_web_app_url(web_app_url)
    
    # Build first row: mini app button (if valid) + Deposit
    if can_use_mini_app:
        # Mini app button (web_app) - appears on left side
        mini_app_button = KeyboardButton(
            text="📱 Open App",
            web_app=WebAppInfo(url=web_app_url)
        )
        first_row = [mini_app_button, KeyboardButton(text="💵 Deposit")]
    else:
        # Skip mini app button if URL is invalid (HTTP or localhost), just show Deposit
        first_row = [KeyboardButton(text="💵 Deposit")]
    
    keyboard = [
        first_row,
        [KeyboardButton(text="💸 Withdraw")],
        [KeyboardButton(text="📜 History")],
        [KeyboardButton(text="🌐 Open in Browser")],  # Changed from "Open Web App" to "Open in Browser"
        [KeyboardButton(text="ℹ️ Help")],
    ]
    if show_logout:
        keyboard.append([KeyboardButton(text="🚪 Logout")])
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

