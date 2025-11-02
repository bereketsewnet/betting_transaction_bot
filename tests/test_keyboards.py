"""Tests for keyboard builders."""
from app.utils.keyboards import (
    build_inline_keyboard,
    build_paginated_inline_keyboard,
    build_main_menu_keyboard,
)


def test_build_inline_keyboard():
    """Test inline keyboard builder."""
    buttons = [
        ("Button 1", "callback:1"),
        ("Button 2", "callback:2"),
        ("Button 3", "callback:3"),
    ]
    keyboard = build_inline_keyboard(buttons, row_width=2)
    
    assert len(keyboard.inline_keyboard) == 2  # 2 rows (2 + 1)
    assert len(keyboard.inline_keyboard[0]) == 2
    assert len(keyboard.inline_keyboard[1]) == 1


def test_build_paginated_inline_keyboard():
    """Test paginated keyboard builder."""
    items = [(f"Item {i}", f"item:{i}") for i in range(10)]
    keyboard, total_pages = build_paginated_inline_keyboard(
        items, page=1, items_per_page=6
    )
    
    assert total_pages == 2  # 10 items / 6 per page = 2 pages
    assert len(keyboard.inline_keyboard) == 7  # 6 items + 1 nav row


def test_build_main_menu_keyboard():
    """Test main menu keyboard builder."""
    keyboard = build_main_menu_keyboard()
    assert len(keyboard.keyboard) == 5  # 5 rows
    assert keyboard.resize_keyboard == True

