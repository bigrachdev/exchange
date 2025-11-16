
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Import config
from config import BOT_TOKEN, ADMIN_IDS
import config

# Import handlers
from handlers.main_handlers import register_main_handlers
from handlers.sell_handlers import register_sell_handlers
from handlers.buy_handlers import register_buy_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.withdraw_handlers import register_withdraw_handlers

# Import utilities
from database import init_db
from keep_alive import keep_alive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Register all handlers - ORDER MATTERS!
register_main_handlers(dp)
register_sell_handlers(dp)
register_buy_handlers(dp)
register_withdraw_handlers(dp)
register_admin_handlers(dp)

async def on_startup(dispatcher):
    """Execute on bot startup"""
    # Start keep-alive server
    keep_alive()
    
    # Delete webhook to clear any conflicts
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("✅ Webhook deleted, ready for polling")
    except Exception as e:
        logging.error(f"❌ Error deleting webhook: {e}")
    
    # Wait for webhook to clear
    await asyncio.sleep(2)
    
    # Initialize database
    init_db()
    logging.info("✅ Database initialized")
    
    # Get bot info
    me = await bot.get_me()
    config.BOT_USERNAME = me.username
    logging.info(f"✅ Bot started: @{me.username} (ID: {me.id})")
    logging.info("🔥 Polling mode active - Bot will stay alive!")
    
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🚀 **Bot Started Successfully!**\n\n"
                f"Bot: @{me.username}\n"
                "Status: ✅ Online\n"
                "Mode: Polling with Keep-Alive\n\n"
                "Use /admin to access admin panel",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

async def on_shutdown(dispatcher):
    """Execute on bot shutdown"""
    logging.info("⚠️ Shutting down bot...")
    
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
    
    # Close bot session
    await bot.close()
    logging.info("✅ Bot shutdown complete")

if __name__ == '__main__':
    logging.info("🚀 Starting TOPO EXCHANGE Bot...")
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )