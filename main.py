# main.py - Entry point for the bot application
# This file sets up the bot, dispatcher, and webhook for hosting on Render.

import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # type: ignore
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, ADMIN_IDS
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

async def on_startup(dp):
    init_db()  # Initialize database
    me = await bot.get_me()
    config.BOT_USERNAME = me.username
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logging.info("Webhook set")

async def on_shutdown(dp):
    await bot.delete_webhook()
    logging.info("Webhook removed")

if __name__ == '__main__':
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=8080  # Render listens on port 8080 or environment PORT
    )