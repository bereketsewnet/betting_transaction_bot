# Troubleshooting Guide

## Bot Conflict Error

If you see this error:
```
TelegramConflictError: Telegram server says - Conflict: terminated by other getUpdates request; 
make sure that only one bot instance is running
```

This means **another instance of your bot is already running**. Here's how to fix it:

### Solution 1: Stop Other Instances

1. **Check for running processes**:
   - On Windows: Open Task Manager (Ctrl+Shift+Esc)
   - Look for Python processes running `app.bot` or `python -m app.bot`
   - End those processes

2. **Check other terminal windows**:
   - Close any other PowerShell/Command Prompt windows running the bot
   - Make sure you're not running it twice

3. **Check for webhook**:
   - If you previously set up a webhook, it might still be active
   - Delete the webhook using:
     ```python
     import asyncio
     from aiogram import Bot
     
     async def delete_webhook():
         bot = Bot(token="YOUR_BOT_TOKEN")
         await bot.delete_webhook(drop_pending_updates=True)
         print("Webhook deleted!")
         await bot.session.close()
     
     asyncio.run(delete_webhook())
     ```

### Solution 2: Delete Webhook (if using webhook mode)

If you switched from webhook to polling mode, delete the webhook:

```powershell
# Using the script
python scripts/delete_webhook.py

# Or manually
python -c "import asyncio; from aiogram import Bot; bot = Bot(token='YOUR_TOKEN'); asyncio.run(bot.delete_webhook(drop_pending_updates=True))"
```

### Solution 3: Wait and Retry

Sometimes Telegram needs a few seconds to release the bot. Wait 10-20 seconds and try again.

## Common Issues

### 1. RuntimeWarning about coroutine

**Error**: `RuntimeWarning: coroutine 'on_startup' was never awaited`

**Fix**: This is fixed in the code. Make sure you're using the latest version.

### 2. Import Errors

**Error**: `ImportError: cannot import name...`

**Fix**: Make sure:
- Virtual environment is activated: `.venv\Scripts\Activate.ps1`
- You're using Python 3.12: `python --version`
- All dependencies are installed: `pip install -r requirements.txt`

### 3. Configuration Errors

**Error**: `ValueError: TELEGRAM_BOT_TOKEN is required`

**Fix**: 
- Create `.env` file in project root
- Add your bot token: `TELEGRAM_BOT_TOKEN=your_token_here`
- Make sure the file is named exactly `.env` (not `.env.txt`)

### 4. API Connection Errors

**Error**: Connection errors when calling backend API

**Fix**:
- Check `API_BASE_URL` in `.env`
- Make sure backend server is running
- Verify the URL is correct (including `/api/v1`)

## Quick Fix Commands

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Delete webhook
python -c "import asyncio; from aiogram import Bot; from app.config import config; bot = Bot(token=config.TELEGRAM_BOT_TOKEN); asyncio.run(bot.delete_webhook(drop_pending_updates=True)); asyncio.run(bot.session.close())"

# Check if bot is running
Get-Process python | Where-Object {$_.CommandLine -like "*app.bot*"}

# Restart bot cleanly
# 1. Stop any running instances (Ctrl+C in terminal)
# 2. Delete webhook (see above)
# 3. Wait 5 seconds
# 4. Start again: python -m app.bot --mode polling
```

