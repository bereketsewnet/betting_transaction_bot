"""Script to manage Telegram webhook (set/delete/get info)."""
import asyncio
import argparse
import sys
from app.config import config
from app.logger import logger
from aiogram import Bot


async def delete_webhook():
    """Delete webhook and drop pending updates."""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return False
    
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    try:
        result = await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted successfully!")
        logger.info(f"Pending updates dropped: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Error deleting webhook: {e}")
        return False
    finally:
        await bot.session.close()


async def set_webhook():
    """Set webhook URL."""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return False
    
    if not config.WEBHOOK_URL:
        logger.error("WEBHOOK_URL not set in .env file")
        logger.error("Please set WEBHOOK_URL in .env before setting webhook")
        return False
    
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    try:
        result = await bot.set_webhook(
            url=config.WEBHOOK_URL,
            secret_token=config.WEBHOOK_SECRET_TOKEN,
            drop_pending_updates=True,
        )
        logger.info(f"✅ Webhook set successfully to: {config.WEBHOOK_URL}")
        logger.info(f"Result: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        return False
    finally:
        await bot.session.close()


async def get_webhook_info():
    """Get current webhook information."""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return
    
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    try:
        info = await bot.get_webhook_info()
        logger.info("📋 Current Webhook Info:")
        logger.info(f"   URL: {info.url or 'Not set'}")
        logger.info(f"   Has custom certificate: {info.has_custom_certificate}")
        logger.info(f"   Pending update count: {info.pending_update_count}")
        if info.last_error_date:
            logger.warning(f"   Last error date: {info.last_error_date}")
        if info.last_error_message:
            logger.warning(f"   Last error: {info.last_error_message}")
        if info.max_connections:
            logger.info(f"   Max connections: {info.max_connections}")
        if info.allowed_updates:
            logger.info(f"   Allowed updates: {info.allowed_updates}")
    except Exception as e:
        logger.error(f"❌ Error getting webhook info: {e}")
    finally:
        await bot.session.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage Telegram webhook")
    parser.add_argument(
        "action",
        choices=["delete", "set", "info"],
        help="Action to perform: delete, set, or info"
    )
    
    args = parser.parse_args()
    
    if args.action == "delete":
        asyncio.run(delete_webhook())
    elif args.action == "set":
        asyncio.run(set_webhook())
    elif args.action == "info":
        asyncio.run(get_webhook_info())


if __name__ == "__main__":
    main()

