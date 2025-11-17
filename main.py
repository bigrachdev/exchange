# main.py - FIXED VERSION
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

# Register all handlers
register_main_handlers(dp)
register_sell_handlers(dp)
register_buy_handlers(dp)
register_withdraw_handlers(dp)
register_admin_handlers(dp)

async def on_startup(dispatcher):
    """Execute on bot startup"""
    logging.info("🚀 Bot startup initiated...")
    
    # Start keep-alive server FIRST
    keep_alive()
    
    # CRITICAL: Proper webhook cleanup for Render
    try:
        logging.info("🔄 Clearing webhooks...")
        
        # Method 1: Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(2)
        
        # Method 2: Set empty webhook to be sure
        await bot.set_webhook("")
        await asyncio.sleep(1)
        
        logging.info("✅ Webhooks cleared successfully")
        
    except Exception as e:
        logging.warning(f"⚠️ Webhook cleanup warning: {e}")
    
    # Initialize database
    init_db()
    logging.info("✅ Database initialized")
    
    # Get bot info
    try:
        me = await bot.get_me()
        config.BOT_USERNAME = me.username
        logging.info(f"✅ Bot authenticated: @{me.username} (ID: {me.id})")
        
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
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id}: {e}")
                
    except Exception as e:
        logging.error(f"❌ Bot authentication failed: {e}")
        raise

async def on_shutdown(dispatcher):
    """Execute on bot shutdown"""
    logging.info("⚠️ Bot shutting down...")
    
    # Clean shutdown
    try:
        await bot.delete_webhook()
        logging.info("✅ Webhook cleaned up")
    except:
        pass
    
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
    
    await bot.close()
    logging.info("✅ Bot shutdown complete")

if __name__ == '__main__':
    logging.info("🚀 Starting TOPO EXCHANGE Bot...")
    
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=60,      # Longer timeout
            relax=1.0,       # Slower polling
            fast=True        # Better for production
        )
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
        # Don't attempt restart - let Render handle it