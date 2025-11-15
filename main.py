# main.py - Entry point for the bot application with health check endpoint

import logging
import os
import asyncio
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
    return web.Response(text="🤖 TOPO EXCHANGE Bot is running!", status=200)

async def on_startup(dp):
    """Execute on bot startup"""
    # Delete webhook to ensure polling works
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Webhook deleted, ready for polling")
    
    # Initialize database
    init_db()
    logging.info("✅ Database initialized")
    
    # Get bot info
    me = await bot.get_me()
    config.BOT_USERNAME = me.username
    logging.info(f"✅ Bot started: @{me.username} (ID: {me.id})")
    
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🚀 **Bot Started Successfully!**\n\n"
                f"Bot: @{me.username}\n"
                "Status: ✅ Online\n"
                "Mode: Polling\n\n"
                "Use /admin to access admin panel",
                parse_mode="Markdown"
            )
        except:
            pass

async def start_webhook_server():
    """Start web server in background"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"✅ Health check server started on port {port}")
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)

async def on_shutdown(dp):
    """Cleanup on shutdown"""
    logging.info("⚠️ Shutting down bot...")
    
    # Close bot session
    await bot.close()
    
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "⚠️ **Bot Shutting Down**\n\nStatus: Offline",
                parse_mode="Markdown"
            )
        except:
            pass
    
    logging.info("✅ Bot shutdown complete")

if __name__ == '__main__':
    # Start health check server in background
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook_server())
    
    # Start bot polling
    executor.start_polling(
        dp, 
        skip_updates=True, 
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )