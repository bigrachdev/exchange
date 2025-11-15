# main.py - Entry point for the bot application with health check endpoint

import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from handlers.main_handlers import register_main_handlers
from handlers.sell_handlers import register_sell_handlers
from handlers.buy_handlers import register_buy_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.withdraw_handlers import register_withdraw_handlers
from database import init_db
import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Register all handlers
register_main_handlers(dp)
register_sell_handlers(dp)
register_buy_handlers(dp)
register_withdraw_handlers(dp)
register_admin_handlers(dp)

async def health_check(request):
    """Health check endpoint for Render"""
    return web.Response(text="Bot is running!", status=200)

async def on_startup(dp):
    # Delete webhook to ensure polling works
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook deleted, ready for polling")
    
    init_db()  # Initialize database
    me = await bot.get_me()
    config.BOT_USERNAME = me.username
    logging.info(f"Bot started: {me.username}")
    
    # Start health check web server
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Health check server started on port {port}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)