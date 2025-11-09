"""Main bot file with polling and webhook support."""
import asyncio
import argparse
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import config
from app.logger import logger
from app.storage import get_storage
from app.services.api_client import APIClient
from app.services.notify_service import NotifyService
from app.middlewares.error_handler import ErrorHandlerMiddleware, error_handler

# Import handlers
from app.handlers import start, main_menu, deposit_flow, withdraw_flow, history, inline_lists, callbacks, admin_menu


async def setup_handlers(dp: Dispatcher, api_client: APIClient, storage):
    """Register all handlers."""
    # Register routers
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(deposit_flow.router)
    dp.include_router(withdraw_flow.router)
    dp.include_router(history.router)
    dp.include_router(inline_lists.router)
    dp.include_router(callbacks.router)
    dp.include_router(admin_menu.router)


async def on_startup(bot: Bot, api_client: APIClient, storage):
    """Startup handler."""
    logger.info("Bot starting up...")
    
    # Log API configuration for backend whitelisting
    logger.info("=" * 60)
    logger.info("🔧 Bot Configuration:")
    logger.info(f"   API Base URL: {config.API_BASE_URL}")
    logger.info(f"   Bot Token: {config.TELEGRAM_BOT_TOKEN[:10]}... (hidden)")
    logger.info(f"   Storage Mode: {config.STORAGE_MODE}")
    if config.API_BASE_URL:
        from urllib.parse import urlparse
        parsed = urlparse(config.API_BASE_URL)
        logger.info(f"   API Host: {parsed.netloc}")
        logger.info(f"   API Scheme: {parsed.scheme}")
        logger.info("")
        logger.info("📋 To whitelist in your backend, allow requests from:")
        logger.info(f"   Host: {parsed.netloc}")
        logger.info(f"   Origin: {parsed.scheme}://{parsed.netloc}")
    logger.info("=" * 60)
    
    # Close existing webhook if any
    await bot.delete_webhook(drop_pending_updates=True)
    
    if config.USE_WEBHOOK:
        # Set webhook
        await bot.set_webhook(
            url=config.WEBHOOK_URL,
            secret_token=config.WEBHOOK_SECRET_TOKEN,
        )
        logger.info(f"Webhook set to: {config.WEBHOOK_URL}")
    else:
        logger.info("Bot running in polling mode")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    logger.info("✅ Bot is ready!")


async def on_shutdown(bot: Bot, api_client: APIClient, storage):
    """Shutdown handler."""
    logger.info("Bot shutting down...")
    await bot.delete_webhook(drop_pending_updates=True)
    await api_client.close()
    await storage.close()
    logger.info("Bot shut down complete")


async def polling_mode():
    """Run bot in polling mode."""
    logger.info("Starting bot in polling mode...")
    
    # Initialize dependencies
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    storage = get_storage()
    api_client = APIClient()
    
    # Initialize Dispatcher with FSM storage
    from aiogram.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage
    dp = Dispatcher(storage=AiogramMemoryStorage())
    
    # Setup dependency injection middleware FIRST
    # This must run before other middleware so dependencies are available
    async def inject_dependencies(handler, event, data):
        """Inject dependencies into handlers."""
        # Put dependencies in data dict - aiogram will extract them for handler parameters
        data["api_client"] = api_client
        data["storage"] = storage
        return await handler(event, data)
    
    dp.message.middleware(inject_dependencies)
    dp.callback_query.middleware(inject_dependencies)
    
    # Register other middlewares AFTER dependency injection
    # NO throttling - let users interact naturally
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.errors.register(error_handler)
    
    # Setup handlers
    await setup_handlers(dp, api_client, storage)
    
    # Register startup/shutdown handlers
    async def startup_wrapper():
        await on_startup(bot, api_client, storage)
    
    async def shutdown_wrapper():
        await on_shutdown(bot, api_client, storage)
    
    dp.startup.register(startup_wrapper)
    dp.shutdown.register(shutdown_wrapper)
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()
        await api_client.close()
        await storage.close()


async def webhook_mode():
    """Run bot in webhook mode."""
    logger.info("Starting bot in webhook mode...")
    
    if not config.WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL is required for webhook mode")
    
    # Initialize dependencies
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    storage = get_storage()
    api_client = APIClient()
    
    # Initialize Dispatcher with FSM storage
    from aiogram.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage
    dp = Dispatcher(storage=AiogramMemoryStorage())
    
    # Setup dependency injection middleware FIRST
    # This must run before other middleware so dependencies are available
    async def inject_dependencies(handler, event, data):
        """Inject dependencies into handlers."""
        # Put dependencies in data dict - aiogram will extract them for handler parameters
        data["api_client"] = api_client
        data["storage"] = storage
        return await handler(event, data)
    
    dp.message.middleware(inject_dependencies)
    dp.callback_query.middleware(inject_dependencies)
    
    # Register other middlewares AFTER dependency injection
    # NO throttling - let users interact naturally
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.errors.register(error_handler)
    
    # Setup handlers
    await setup_handlers(dp, api_client, storage)
    
    # Register startup/shutdown handlers
    async def startup_wrapper():
        await on_startup(bot, api_client, storage)
    
    async def shutdown_wrapper():
        await on_shutdown(bot, api_client, storage)
    
    dp.startup.register(startup_wrapper)
    dp.shutdown.register(shutdown_wrapper)
    
    # Create aiohttp app
    app = web.Application()
    
    # Create webhook handler
    webhook_path = "/webhook"
    request_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.WEBHOOK_SECRET_TOKEN,
    )
    request_handler.register(app, path=webhook_path)
    
    # Setup notify webhook
    notify_service = NotifyService(bot, storage, api_client)
    
    async def notify_handler(request):
        """Handle backend notifications."""
        # Verify secret
        secret = request.headers.get("X-BACKEND-SECRET")
        if secret != config.BACKEND_NOTIFY_SECRET:
            logger.warning("Invalid notify secret")
            return web.Response(status=401, text="Unauthorized")
        
        # Process notification
        try:
            data = await request.json()
            await notify_service.handle_backend_notification(data)
            return web.Response(status=200, text="OK")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    # Setup notify endpoint
    app.router.add_post("/notify", notify_handler)
    
    # Setup aiogram application
    setup_application(app, dp, bot=bot)
    
    # Run webhook server
    logger.info(f"✅ Bot is running at http://{config.APP_HOST}:{config.APP_PORT}")
    logger.info(f"Webhook URL: {config.WEBHOOK_URL}")
    logger.info(f"Notify endpoint: http://{config.APP_HOST}:{config.APP_PORT}/notify")
    
    web.run_app(app, host=config.APP_HOST, port=config.APP_PORT)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Betting Transaction Bot")
    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="Bot mode (default: polling)",
    )
    args = parser.parse_args()
    
    if args.mode == "polling":
        asyncio.run(polling_mode())
    else:
        asyncio.run(webhook_mode())


if __name__ == "__main__":
    main()

