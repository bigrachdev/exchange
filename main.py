# main.py - FIXED VERSION FOR RENDER
import logging
import asyncio
import os
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

# Global flag to track if bot is running
BOT_RUNNING = False

async def setup_bot():
    """Setup bot with proper cleanup"""
    logging.info("🔄 Setting up bot...")
    
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
    
    return bot, dp

async def on_startup(dispatcher):
    """Execute on bot startup"""
    global BOT_RUNNING
    
    if BOT_RUNNING:
        logging.warning("⚠️ Bot already running, skipping startup")
        return
        
    BOT_RUNNING = True
    logging.info("🚀 Bot startup initiated...")
    
    # Start keep-alive server
    keep_alive()
    
    # CRITICAL: Force webhook cleanup
    try:
        logging.info("🔄 Force-clearing webhooks...")
        
        # Multiple methods to ensure webhook is cleared
        await dispatcher.bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(3)
        
        # Set empty webhook to be absolutely sure
        await dispatcher.bot.set_webhook("")
        await asyncio.sleep(2)
        
        logging.info("✅ Webhooks completely cleared")
        
    except Exception as e:
        logging.error(f"❌ Webhook cleanup failed: {e}")
        # Continue anyway - sometimes this fails but polling still works
    
    # Initialize database
    init_db()
    logging.info("✅ Database initialized")
    
    # Get bot info
    try:
        me = await dispatcher.bot.get_me()
        config.BOT_USERNAME = me.username
        logging.info(f"✅ Bot authenticated: @{me.username} (ID: {me.id})")
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await dispatcher.bot.send_message(
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
    global BOT_RUNNING
    logging.info("⚠️ Bot shutting down...")
    
    # Clean shutdown
    try:
        await dispatcher.bot.delete_webhook()
        logging.info("✅ Webhook cleaned up")
    except Exception as e:
        logging.warning(f"⚠️ Webhook cleanup warning: {e}")
    
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await dispatcher.bot.send_message(
                admin_id,
                "⚠️ **Bot Shutting Down**\n\nStatus: Offline",
                parse_mode="Markdown"
            )
        except:
            pass
    
    BOT_RUNNING = False
    logging.info("✅ Bot shutdown complete")

def main():
    """Main entry point"""
    logging.info("🚀 Starting TOPO EXCHANGE Bot...")
    
    try:
        # Use asyncio to run the setup
        bot, dp = asyncio.run(setup_bot())
        
        # Start polling with error handling
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=60,
            relax=2.0,  # Slower polling to avoid conflicts
            fast=False   # Disable fast mode for stability
        )
    except KeyboardInterrupt:
        logging.info("⏹️ Bot stopped by user")
    except Exception as e:
        logging.error(f"❌ Bot crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()