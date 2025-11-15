# Bot Template Keys Documentation

This document lists all template keys used in the Telegram bot. Each key should be created in the `templates` table with different language codes.

## Template Key Format

- **Key Name**: `key_name` in database
- **Language Code**: `language_code` in database (e.g., 'en', 'am')
- **Content**: `content` in database (the actual message text)

## Fallback Behavior

- If a template is not found for the requested language, the bot will automatically fallback to English ('en')
- If English template is also not found, the bot will use a hardcoded default (shown in this document)

---

## Start & Authentication

### `welcome_message`
**Default English**: (empty - user has their own)
**Usage**: Welcome message shown after language selection
**Location**: `start.py` - `select_language()`

### `start_language_selection`
**Default English**: `👋 Welcome! Please select your preferred language:`
**Usage**: Initial language selection prompt
**Location**: `start.py` - `cmd_start()`

### `start_what_to_do`
**Default English**: `What would you like to do?`
**Usage**: Question after welcome message
**Location**: `start.py` - `select_language()`

### `button_register`
**Default English**: `📝 Register`
**Usage**: Register button text
**Location**: `start.py` - `select_language()`

### `button_login`
**Default English**: `🔐 Login`
**Usage**: Login button text
**Location**: `start.py` - `select_language()`

### `button_continue_guest`
**Default English**: `👤 Continue as Guest`
**Usage**: Continue as guest button text
**Location**: `start.py` - `select_language()`

### `guest_created_success`
**Default English**: `✅ You are now using the bot as a guest.\n\nYou can make transactions, but some features may be limited.\nTo access all features, please register.`
**Usage**: Message when user continues as guest
**Location**: `start.py` - `continue_as_guest()`

### `login_enter_username`
**Default English**: `🔐 Login\n\nPlease enter your username (email):`
**Usage**: Prompt for username during login
**Location**: `start.py` - `start_login()`

### `login_enter_password`
**Default English**: `Please enter your password:`
**Usage**: Prompt for password during login
**Location**: `start.py` - `process_login_password()`

### `login_success`
**Default English**: `✅ Login successful! Welcome back to Betting Payment Manager!`
**Usage**: Success message after login
**Location**: `start.py` - `process_login_password()`

### `login_failed`
**Default English**: `❌ Login failed. Please check your credentials and try again.`
**Usage**: Error message when login fails
**Location**: `start.py` - `process_login_password()`

### `register_enter_email`
**Default English**: `📝 Registration\n\nPlease enter your email address:`
**Usage**: Prompt for email during registration
**Location**: `start.py` - `start_registration()`

### `register_enter_password`
**Default English**: `Please enter your password (min 6 characters):`
**Usage**: Prompt for password during registration
**Location**: `start.py` - `process_registration_password()`

### `register_enter_display_name`
**Default English**: `Please enter your display name:`
**Usage**: Prompt for display name during registration
**Location**: `start.py` - `process_registration_display_name()`

### `register_enter_phone`
**Default English**: `Please enter your phone number (optional):`
**Usage**: Prompt for phone during registration
**Location**: `start.py` - `process_registration_phone()`

### `register_success`
**Default English**: `✅ Registration successful! Welcome to Betting Payment Manager!`
**Usage**: Success message after registration
**Location**: `start.py` - `process_phone()`

### `error_no_languages`
**Default English**: `No languages available. Please contact support.`
**Usage**: Error when no languages available
**Location**: `start.py` - `cmd_start()`

### `error_start_failed`
**Default English**: `❌ An error occurred while starting the bot.\n\nError: {error_type}\nPlease try again or contact support.`
**Usage**: Generic error during start
**Location**: `start.py` - `cmd_start()`

### `error_generic`
**Default English**: `❌ An error occurred. Please try again.`
**Usage**: Generic error message
**Location**: Multiple files

---

## Main Menu

### `main_menu_title`
**Default English**: `🏠 Main Menu\n\nSelect an option:`
**Usage**: Main menu title
**Location**: `main_menu.py` - `show_main_menu()`

### `button_deposit`
**Default English**: `💵 Deposit`
**Usage**: Deposit button text
**Location**: `main_menu.py` - `show_main_menu()`

### `button_withdraw`
**Default English**: `💸 Withdraw`
**Usage**: Withdraw button text
**Location**: `main_menu.py` - `show_main_menu()`

### `button_history`
**Default English**: `📜 History`
**Usage**: History button text
**Location**: `main_menu.py` - `show_main_menu()`

### `button_open_browser`
**Default English**: `🌐 Open in Browser`
**Usage**: Open in browser button text
**Location**: `main_menu.py` - `show_main_menu()`

### `button_help`
**Default English**: `ℹ️ Help`
**Usage**: Help button text
**Location**: `main_menu.py` - `show_main_menu()`

### `button_logout`
**Default English**: `🚪 Logout`
**Usage**: Logout button text
**Location**: `main_menu.py` - `show_main_menu()`

### `admin_redirect_message`
**Default English**: `👑 You are logged in as admin. Use the Admin Panel to manage transactions.`
**Usage**: Message when admin tries to use player features
**Location**: `main_menu.py` - `cmd_deposit()`, `cmd_withdraw()`, `cmd_history()`

### `agent_redirect_message`
**Default English**: `👤 You are logged in as agent. Use the Agent Panel to manage your assigned transactions.`
**Usage**: Message when agent tries to use player features
**Location**: `main_menu.py` - `cmd_deposit()`, `cmd_withdraw()`, `cmd_history()`

### `web_app_description`
**Default English**: `🌐 Web App\n\nClick the button below to open the web app in your browser:`
**Usage**: Web app description
**Location**: `main_menu.py` - `cmd_web_app()`

### `help_text`
**Default English**: `ℹ️ Help\n\nAvailable commands:\n• /start - Start the bot\n• /menu - Show main menu\n• /logout - Logout from your account\n• /help - Show this help message\n\nMain features:\n• 💵 Deposit - Make a deposit transaction\n• 💸 Withdraw - Make a withdrawal transaction\n• 📜 History - View your transaction history\n• 📱 Open App - Open mini app (Telegram Web App)\n• 🌐 Open in Browser - Open web app in browser\n• 🚪 Logout - Logout and login with another account\n\nFor support, please contact the administrator.`
**Usage**: Help message content
**Location**: `main_menu.py` - `cmd_help()`

### `logout_not_logged_in`
**Default English**: `ℹ️ You are not logged in. Nothing to logout.`
**Usage**: Message when user tries to logout but not logged in
**Location**: `main_menu.py` - `cmd_logout()`

### `logout_success`
**Default English**: `✅ Logout successful!\n\nYou can now:\n• /start - Login with another account\n• Continue as guest`
**Usage**: Success message after logout
**Location**: `main_menu.py` - `cmd_logout()`

### `logout_local_success`
**Default English**: `✅ Logged out locally.\n\nNote: Backend logout may have failed, but you can still login with another account.`
**Usage**: Message when local logout succeeds but API fails
**Location**: `main_menu.py` - `cmd_logout()`

---

## Deposit Flow

### `deposit_title`
**Default English**: `💵 Deposit\n\nSelect a deposit bank:`
**Usage**: Deposit flow start message
**Location**: `deposit_flow.py` - `start_deposit_flow()`

### `error_no_deposit_banks`
**Default English**: `❌ No deposit banks available. Please contact support.`
**Usage**: Error when no deposit banks available
**Location**: `deposit_flow.py` - `start_deposit_flow()`

### `error_bank_not_found`
**Default English**: `❌ Bank not found.`
**Usage**: Error when bank not found
**Location**: `deposit_flow.py` - `select_deposit_bank()`

### `deposit_enter_amount`
**Default English**: `Enter the deposit amount:`
**Usage**: Prompt for deposit amount
**Location**: `deposit_flow.py` - `select_deposit_bank()`

### `error_invalid_amount`
**Default English**: `❌ Invalid amount. Please enter a valid number greater than 0.`
**Usage**: Error for invalid amount
**Location**: `deposit_flow.py` - `process_deposit_amount()`

### `deposit_select_betting_site`
**Default English**: `Select a betting site:`
**Usage**: Prompt to select betting site
**Location**: `deposit_flow.py` - `process_deposit_amount()`

### `error_no_betting_sites`
**Default English**: `❌ No betting sites available. Please contact support.`
**Usage**: Error when no betting sites available
**Location**: `deposit_flow.py` - `process_deposit_amount()`

### `deposit_enter_player_site_id`
**Default English**: `Enter your player ID on the betting site:`
**Usage**: Prompt for player site ID
**Location**: `deposit_flow.py` - `select_betting_site()`

### `error_invalid_player_site_id`
**Default English**: `❌ Invalid player ID. Please enter a valid player ID.`
**Usage**: Error for invalid player site ID
**Location**: `deposit_flow.py` - `process_player_site_id()`

### `deposit_upload_screenshot`
**Default English**: `Upload a screenshot of your payment:`
**Usage**: Prompt to upload screenshot
**Location**: `deposit_flow.py` - `process_player_site_id()`

### `error_invalid_file`
**Default English**: `❌ Invalid file. Please send a photo (PNG, JPG, or JPEG).`
**Usage**: Error for invalid file type
**Location**: `deposit_flow.py` - `process_screenshot()`

### `error_file_too_large`
**Default English**: `❌ File is too large. Maximum size is 5MB.`
**Usage**: Error for file too large
**Location**: `deposit_flow.py` - `process_screenshot()`

### `deposit_confirm`
**Default English**: `Please confirm your deposit:\n\nAmount: {currency} {amount}\nBank: {bank_name}\nBetting Site: {site_name}\nPlayer ID: {player_site_id}`
**Usage**: Deposit confirmation message
**Location**: `deposit_flow.py` - `process_screenshot()`

### `button_confirm`
**Default English**: `✅ Confirm`
**Usage**: Confirm button text
**Location**: `deposit_flow.py` - `process_screenshot()`

### `button_cancel`
**Default English**: `❌ Cancel`
**Usage**: Cancel button text
**Location**: `deposit_flow.py` - `process_screenshot()`

### `deposit_processing`
**Default English**: `⏳ Processing your deposit, please wait...`
**Usage**: Message while processing deposit
**Location**: `deposit_flow.py` - `confirm_deposit()`

### `transaction_created`
**Default English**: `✅ Your transaction has been created successfully!\n\nTransaction ID: {transaction_uuid}\nAmount: {currency} {amount}\nStatus: {status}\n\nYou can check the status in your transaction history.`
**Usage**: Success message after transaction creation
**Location**: `deposit_flow.py` - `confirm_deposit()`

### `transaction_processed`
**Default English**: `🎉 Your transaction has been processed!\n\nTransaction ID: {transaction_uuid}\nStatus: {status}`
**Usage**: Message when transaction is processed
**Location**: Multiple files

---

## Withdraw Flow

### `withdraw_title`
**Default English**: `💸 Withdraw\n\nSelect a withdrawal bank:`
**Usage**: Withdraw flow start message
**Location**: `withdraw_flow.py` - `start_withdraw_flow()`

### `error_no_withdrawal_banks`
**Default English**: `❌ No withdrawal banks available. Please contact support.`
**Usage**: Error when no withdrawal banks available
**Location**: `withdraw_flow.py` - `start_withdraw_flow()`

### `withdraw_enter_required_field`
**Default English**: `Please enter {field_label}:`
**Usage**: Prompt for required withdrawal field
**Location**: `withdraw_flow.py` - `select_withdraw_bank()`

### `withdraw_enter_amount`
**Default English**: `Enter the withdrawal amount:`
**Usage**: Prompt for withdrawal amount
**Location**: `withdraw_flow.py` - `process_required_fields()`

### `withdraw_enter_address`
**Default English**: `Enter your withdrawal address:`
**Usage**: Prompt for withdrawal address
**Location**: `withdraw_flow.py` - `process_withdraw_amount()`

### `withdraw_confirm`
**Default English**: `Please confirm your withdrawal:\n\nAmount: {currency} {amount}\nBank: {bank_name}\nAddress: {address}\nBetting Site: {site_name}\nPlayer ID: {player_site_id}`
**Usage**: Withdrawal confirmation message
**Location**: `withdraw_flow.py` - `process_withdraw_address()`

---

## Transaction History

### `history_title`
**Default English**: `📜 Transaction History\n\nFound {count} transaction(s). Select one to view details:`
**Usage**: History list title
**Location**: `history.py` - `show_transaction_history()`

### `history_empty`
**Default English**: `📜 Transaction History\n\nNo transactions found.`
**Usage**: Message when no transactions found
**Location**: `history.py` - `show_transaction_history()`

### `error_history_failed`
**Default English**: `❌ An error occurred while fetching transaction history.\n\n{error_details}`
**Usage**: Error when history fetch fails
**Location**: `history.py` - `show_transaction_history()`

### `error_transaction_not_found`
**Default English**: `❌ Player not found.`
**Usage**: Error when transaction not found
**Location**: `history.py` - `show_transaction_details()`

### `error_transaction_details_failed`
**Default English**: `❌ Failed to load transaction details.`
**Usage**: Error when transaction details fail to load
**Location**: `history.py` - `show_transaction_details()`

### `button_back`
**Default English**: `🔙 Back`
**Usage**: Back button text
**Location**: Multiple files

---

## Admin Menu

### `admin_menu_title`
**Default English**: `👑 Admin Panel\n\nSelect an option:`
**Usage**: Admin menu title
**Location**: `admin_menu.py` - `show_admin_menu()`

### `button_all_transactions`
**Default English**: `📋 All Transactions`
**Usage**: All transactions button text
**Location**: `admin_menu.py` - `show_admin_menu()`

### `button_recent_24h`
**Default English**: `🕐 Recent (24h)`
**Usage**: Recent 24h button text
**Location**: `admin_menu.py` - `show_admin_menu()`

### `button_by_date`
**Default English**: `📅 By Date`
**Usage**: By date button text
**Location**: `admin_menu.py` - `show_admin_menu()`

### `admin_filter_by_date`
**Default English**: `📅 Filter by Date\n\nPlease enter the date (YYYY-MM-DD):\nExample: 2025-11-08`
**Usage**: Date filter prompt
**Location**: `admin_menu.py` - `request_date_for_message()`

### `error_admin_access_required`
**Default English**: `❌ Please login as admin or agent to use this feature.`
**Usage**: Error when non-admin tries to use admin feature
**Location**: `admin_menu.py` - Multiple functions

---

## Agent Menu

### `agent_menu_title`
**Default English**: `👤 Agent Panel\n\nSelect an option:`
**Usage**: Agent menu title
**Location**: `agent_menu.py` - `show_agent_menu()`

### `button_my_transactions`
**Default English**: `📋 My Transactions`
**Usage**: My transactions button text
**Location**: `agent_menu.py` - `show_agent_menu()`

### `button_my_stats`
**Default English**: `📊 My Stats`
**Usage**: My stats button text
**Location**: `agent_menu.py` - `show_agent_menu()`

### `error_agent_access_required`
**Default English**: `❌ Agent access required.`
**Usage**: Error when non-agent tries to use agent feature
**Location**: `agent_menu.py` - Multiple functions

---

## Navigation Buttons

### `button_prev`
**Default English**: `◀ Prev`
**Usage**: Previous page button
**Location**: `keyboards.py` - `build_paginated_inline_keyboard()`

### `button_next`
**Default English**: `Next ▶`
**Usage**: Next page button
**Location**: `keyboards.py` - `build_paginated_inline_keyboard()`

---

## Error Messages

### `error_connection_failed`
**Default English**: `Cannot connect to server. Please try again.`
**Usage**: Connection error
**Location**: Multiple files

### `error_validation_failed`
**Default English**: `Validation error. Please contact support.`
**Usage**: Validation error
**Location**: Multiple files

### `error_unknown`
**Default English**: `❌ An error occurred. Please try again.`
**Usage**: Generic unknown error
**Location**: Multiple files

---

## Notes

1. **Template Variables**: Some templates use variables like `{amount}`, `{currency}`, etc. These should be replaced with actual values when using the template.

2. **Emoji Support**: All templates support emojis. Make sure to include them in translations if desired.

3. **Line Breaks**: Use `\n` for line breaks in template content.

4. **Creating Templates**: To create a template, insert into the `templates` table:
   ```sql
   INSERT INTO templates (language_code, key_name, content) 
   VALUES ('am', 'welcome_message', 'Your Amharic welcome message here');
   ```

5. **Fallback**: Always create English ('en') templates first as they serve as fallback for missing translations.

