# main.py - PRODUCTION-READY VERSION
import logging
import asyncio
import sys
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
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher GLOBALLY
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Register all handlers ONCE at module level
register_main_handlers(dp)
register_sell_handlers(dp)
register_buy_handlers(dp)
register_withdraw_handlers(dp)
register_admin_handlers(dp)

async def on_startup(dispatcher):
    """Execute on bot startup"""
    logger.info("🚀 Bot startup initiated...")
    
    # Start keep-alive server
    keep_alive()
    
    # CRITICAL: Aggressive webhook cleanup
    try:
        logger.info("🔄 Clearing any existing webhooks and conflicts...")
        
        # Method 1: Delete webhook with drop pending updates
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(2)
        
        # Method 2: Set empty webhook explicitly
        await bot.set_webhook("")
        await asyncio.sleep(2)
        
        # Method 3: Close and reopen session
        await bot.close()
        await asyncio.sleep(2)
        
        logger.info("✅ Webhooks cleared, session reset")
        
    except Exception as e:
        logger.warning(f"⚠️ Webhook cleanup warning: {e}")
        # Continue anyway - polling usually works even if this fails
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Get bot info
    try:
        me = await bot.get_me()
        config.BOT_USERNAME = me.username
        logger.info(f"✅ Bot authenticated: @{me.username} (ID: {me.id})")
        logger.info("🔥 Polling mode active - Bot will stay alive!")
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "🚀 **Bot Started Successfully!**\n\n"
                    f"Bot: @{me.username}\n"
                    f"Status: ✅ Online\n"
                    f"Mode: Long Polling\n\n"
                    f"Use /admin to access admin panel",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Bot authentication failed: {e}")
        raise

async def on_shutdown(dispatcher):
    """Execute on bot shutdown"""
    logger.info("⚠️ Bot shutting down...")
    
    # Clean shutdown
    try:
        await bot.delete_webhook()
        logger.info("✅ Webhook cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Webhook cleanup warning: {e}")
    
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
    
    # Close storage and bot
    await storage.close()
    await storage.wait_closed()
    await bot.close()
    
    logger.info("✅ Bot shutdown complete")

def main():
    """Main entry point"""
    logger.info("🚀 Starting TOPO EXCHANGE Bot...")
    logger.info(f"📋 Configuration:")
    logger.info(f"   - Admins: {len(ADMIN_IDS)}")
    logger.info(f"   - Channel: {config.ADMIN_CHANNEL_ID}")
    logger.info(f"   - Database: {config.DB_NAME}")
    
    try:
        # Start polling with optimized settings
        executor.start_polling(
            dp,
            skip_updates=True,  # Skip old messages
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=30,  # Timeout for long polling
            relax=0.5,  # Delay between failed requests
            fast=False,  # Disable fast mode for stability
            allowed_updates=['message', 'callback_query']  # Only process these
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()