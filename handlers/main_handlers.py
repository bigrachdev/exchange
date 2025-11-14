# handlers/main_handlers.py - Main menu and start handlers

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, get_user_by_referral_code, get_referral_code, get_balance, get_referrals_count, get_pending_rewards_amount, get_paid_rewards_amount, get_user_transactions, get_user_withdrawals
from config import BOT_USERNAME, TOP_COUNTRIES

def register_main_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=['start'])
    dp.register_callback_query_handler(show_main_menu, lambda c: c.data == 'main_menu')
    dp.register_callback_query_handler(rates_handler, lambda c: c.data == 'rates')
    dp.register_callback_query_handler(transactions_handler, lambda c: c.data == 'transactions')
    dp.register_callback_query_handler(help_handler, lambda c: c.data == 'help')
    dp.register_callback_query_handler(refer_earn_handler, lambda c: c.data == 'refer_earn')
    dp.register_callback_query_handler(balance_withdraw_handler, lambda c: c.data == 'balance_withdraw')

async def start_handler(message: types.Message):
    payload = None
    if len(message.text.split()) > 1:
        payload = message.text.split(maxsplit=1)[1]
    referred_by = None
    if payload:
        referrer = get_user_by_referral_code(payload)
        if referrer:
            referred_by = referrer[0]
            await message.answer(f"Welcome! You were referred by @{referrer[1] if referrer[1] else referred_by}. You both can earn rewards!")
    add_user(message.from_user.id, message.from_user.username, referred_by)
    await show_main_menu(message)

async def show_main_menu(message: types.Message | types.CallbackQuery):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛒 Sell Gift Card", callback_data="sell_start"),
        InlineKeyboardButton("💳 Buy Gift Card", callback_data="buy_start"),
        InlineKeyboardButton("📈 Rates", callback_data="rates"),
        InlineKeyboardButton("📜 Transactions", callback_data="transactions"),
        InlineKeyboardButton("👥 Refer & Earn $5", callback_data="refer_earn"),
        InlineKeyboardButton("💰 Balance & Withdraw", callback_data="balance_withdraw"),
        InlineKeyboardButton("🆘 Help", callback_data="help")
    )
    await message.answer("Welcome! Choose an option:", reply_markup=keyboard)

async def rates_handler(query: types.CallbackQuery):
    await query.answer()
    # Fetch and display rates from DB
    await query.message.answer("Rates coming soon... ⬅️ Back", reply_markup=back_keyboard())

async def transactions_handler(query: types.CallbackQuery):
    await query.answer()
    transactions = get_user_transactions(query.from_user.id)
    text = "Your transactions:\n" + "\n".join([str(tx) for tx in transactions]) if transactions else "No transactions."
    await query.message.answer(text + "\n⬅️ Back", reply_markup=back_keyboard())

async def help_handler(query: types.CallbackQuery):
    await query.answer()
    await query.message.answer("Help: Contact @SupportHandle\n⬅️ Back", reply_markup=back_keyboard())

async def refer_earn_handler(query: types.CallbackQuery):
    await query.answer()
    code = get_referral_code(query.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start={code}"
    count = get_referrals_count(query.from_user.id)
    pending = get_pending_rewards_amount(query.from_user.id)
    paid = get_paid_rewards_amount(query.from_user.id)
    text = f"👥 **Refer & Earn $5**\n\nYour referral link:\n`{link}`\n\nShare with friends! Earn $5 when they complete their first successful transaction.\n\nReferred users: {count}\nPending rewards: ${pending:.2f}\nPaid rewards: ${paid:.2f}\n\nNeed help? @SupportHandle"
    await query.message.answer(text, reply_markup=back_keyboard(), parse_mode="Markdown")

async def balance_withdraw_handler(query: types.CallbackQuery):
    await query.answer()
    balance = get_balance(query.from_user.id)
    referrals = get_referrals_count(query.from_user.id)
    pending_rewards = get_pending_rewards_amount(query.from_user.id)
    paid_rewards = get_paid_rewards_amount(query.from_user.id)
    withdrawals = get_user_withdrawals(query.from_user.id)
    wd_text = "\n".join([f"#{wd[0]}: {wd[1]} ${wd[2]:.2f} - {wd[3]}" for wd in withdrawals[:5]]) if withdrawals else "No withdrawals yet."
    text = (
        f"💰 **Balance:** ${balance:.2f}\n\n"
        f"👥 **Referrals:** {referrals}\n"
        f"Pending Rewards: ${pending_rewards:.2f}\n"
        f"Earned Rewards: ${paid_rewards:.2f}\n\n"
        f"**Recent Withdrawals:**\n{wd_text}\n\n"
        f"Need help? @SupportHandle | ⬅️ Back"
    )
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_start"))
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    await query.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

def back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    return keyboard