# handlers/admin_handlers.py - Admin panel handlers

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup  # type: ignore
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, ADMIN_CHANNEL_ID
from database import get_all_users, get_user_transactions, update_rate, get_all_transactions, update_transaction_status, get_available_code, update_balance, reward_exists, add_reward, update_reward_status, get_reward, get_withdrawal, update_withdrawal_status, get_pending_withdrawals, get_transaction, get_referred_by, get_user, add_gift_card, get_all_gift_cards

class AdminAddGiftCard(StatesGroup):
    country = State()
    name = State()
    min_rate = State()
    max_rate = State()

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=['admin'], user_id=ADMIN_IDS)
    dp.register_callback_query_handler(admin_valid, lambda c: c.data.startswith('admin_valid_'))
    dp.register_callback_query_handler(admin_invalid, lambda c: c.data.startswith('admin_invalid_'))
    dp.register_callback_query_handler(complete_tx_handler, lambda c: c.data.startswith('complete_tx_'))
    dp.register_callback_query_handler(reward_paid_handler, lambda c: c.data.startswith('reward_paid_'))
    dp.register_callback_query_handler(wd_approve_handler, lambda c: c.data.startswith('wd_approve_'))
    dp.register_callback_query_handler(wd_deny_handler, lambda c: c.data.startswith('wd_deny_'))
    dp.register_callback_query_handler(admin_users, lambda c: c.data == 'admin_users')
    dp.register_callback_query_handler(admin_transactions, lambda c: c.data == 'admin_transactions')
    dp.register_callback_query_handler(admin_withdrawals, lambda c: c.data == 'admin_withdrawals')
    dp.register_callback_query_handler(admin_rates, lambda c: c.data == 'admin_rates')
    dp.register_callback_query_handler(admin_inventory, lambda c: c.data == 'admin_inventory')
    dp.register_callback_query_handler(admin_gift_cards, lambda c: c.data == 'admin_gift_cards')
    dp.register_callback_query_handler(start_add_gift_card, lambda c: c.data == 'add_gift_card')
    dp.register_message_handler(process_add_country, state=AdminAddGiftCard.country)
    dp.register_message_handler(process_add_name, state=AdminAddGiftCard.name)
    dp.register_message_handler(process_add_min_rate, state=AdminAddGiftCard.min_rate)
    dp.register_message_handler(process_add_max_rate, state=AdminAddGiftCard.max_rate)

async def admin_start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Users", callback_data="admin_users"),
        InlineKeyboardButton("Transactions", callback_data="admin_transactions"),
        InlineKeyboardButton("Withdrawals", callback_data="admin_withdrawals"),
        InlineKeyboardButton("Rates", callback_data="admin_rates"),
        InlineKeyboardButton("Inventory", callback_data="admin_inventory"),
        InlineKeyboardButton("Gift Cards", callback_data="admin_gift_cards")
    )
    await message.answer("Admin Panel", reply_markup=keyboard)

async def admin_users(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    users = get_all_users()
    text = "Users:\n" + "\n".join([f"{u[0]} @{u[1]}" for u in users]) if users else "No users."
    await query.message.answer(text)

async def admin_transactions(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    transactions = get_all_transactions()
    text = "Transactions:\n" + "\n".join([str(tx) for tx in transactions]) if transactions else "No transactions."
    await query.message.answer(text)

async def admin_withdrawals(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    pending = get_pending_withdrawals()
    text = "Pending Withdrawals:\n" + "\n".join([f"{wd[0]}: User {wd[1]} {wd[2]} ${wd[3]}" for wd in pending]) if pending else "No pending withdrawals."
    await query.message.answer(text)

async def admin_rates(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    # For now, simple text; can add states to edit
    await query.message.answer("Rates management: Use /update_rate <gift_card> <country> <min> <max> or implement UI.")

async def admin_inventory(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    # Add inventory management; for now placeholder
    await query.message.answer("Inventory management: Add codes via DB or implement UI.")

async def admin_gift_cards(query: types.CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    gift_cards = get_all_gift_cards()
    text = "Gift Cards:\n" + "\n".join([f"{country}: {name}" for country, name in gift_cards]) if gift_cards else "No gift cards."
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Add New Gift Card", callback_data="add_gift_card"))
    await query.message.answer(text, reply_markup=keyboard)

async def start_add_gift_card(query: types.CallbackQuery, state: FSMContext):
    if query.from_user.id not in ADMIN_IDS:
        return
    await query.answer()
    await query.message.answer("Enter country:")
    await AdminAddGiftCard.country.set()

async def process_add_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("Enter gift card name:")
    await AdminAddGiftCard.name.set()

async def process_add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Enter min rate (default 5.0):")
    await AdminAddGiftCard.min_rate.set()

async def process_add_min_rate(message: types.Message, state: FSMContext):
    min_rate = float(message.text) if message.text else 5.0
    await state.update_data(min_rate=min_rate)
    await message.answer("Enter max rate (default 25.0):")
    await AdminAddGiftCard.max_rate.set()

async def process_add_max_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    max_rate = float(message.text) if message.text else 25.0
    add_gift_card(data['country'], data['name'])
    update_rate(data['name'], data['country'], data['min_rate'], max_rate)
    await message.answer(f"Added {data['name']} for {data['country']} with rates {data['min_rate']}-{max_rate}")
    await state.finish()

async def admin_valid(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    tx_id = query.data.split('_')[2]
    tx = get_transaction(tx_id)
    if tx:
        user_id = tx[1]
        tx_type = tx[2]
        if tx_type == 'sell':
            calculated = tx[5]
            update_transaction_status(tx_id, 'completed')
            update_balance(user_id, calculated)
            await bot.send_message(user_id, f"Your sale is approved! +${calculated:.2f} added to your balance. TX #{tx_id}")
            await query.message.edit_text(query.message.text + "\n✅ Valid - Balance Updated")
            await trigger_referral_reward(tx_id, query.message)
        # For buy, use complete_tx

async def admin_invalid(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    parts = query.data.split('_')
    reason_type = parts[2]
    tx_id = parts[3]
    reason = "Used Code" if reason_type == 'used' else "Invalid Code" if reason_type == 'code' else "Other Issue"
    tx = get_transaction(tx_id)
    if tx:
        update_transaction_status(tx_id, 'failed', reason)
        await bot.send_message(tx[1], f"Sorry, code invalid. Reason: {reason}. TX #{tx_id}. Contact @SupportHandle")
    await query.message.edit_text(query.message.text + f"\nHandled: Invalid - {reason}")

async def complete_tx_handler(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    tx_id = query.data.split('_')[2]
    tx = get_transaction(tx_id)
    if tx and tx[2] == 'buy':
        code = get_available_code(tx[3], tx[4])
        user_id = tx[1]
        if code:
            update_transaction_status(tx_id, 'completed')
            await bot.send_message(user_id, f"Your purchase is confirmed! Gift card code: {code}")
            await query.message.edit_text(query.message.text + "\n✅ Completed")
            await trigger_referral_reward(tx_id, query.message)
        else:
            update_transaction_status(tx_id, 'failed', 'Out of stock')
            await bot.send_message(user_id, "Out of stock. Refund initiated.")
            await query.message.edit_text(query.message.text + "\n❌ Failed - Out of stock")

async def trigger_referral_reward(tx_id, admin_message):
    from main import bot
    tx = get_transaction(tx_id)
    user_id = tx[1]
    referred_by = get_referred_by(user_id)
    if referred_by and not reward_exists(referred_by, user_id):
        reward_id = add_reward(referred_by, user_id, tx_id)
        referrer = get_user(referred_by)
        referred = get_user(user_id)
        text = f"New Referral Reward!\nReferrer: @{referrer[1] if referrer[1] else ''} (ID: {referred_by})\nReferred: @{referred[1] if referred[1] else ''} (ID: {user_id})\nAmount: $5.00\nTX: {tx_id}"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Mark Paid", callback_data=f"reward_paid_{reward_id}"))
        await bot.send_message(ADMIN_CHANNEL_ID, text, reply_markup=kb)

async def reward_paid_handler(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    reward_id = int(query.data.split('_')[2])
    reward = get_reward(reward_id)
    if reward:
        update_reward_status(reward_id, 'paid')
        referrer_id = reward[1]
        amount = reward[3]
        update_balance(referrer_id, amount)
        await bot.send_message(referrer_id, f"Referral reward paid! +${amount:.2f} added to your balance.")
        await query.message.edit_text(query.message.text + "\n✅ Paid")

async def wd_approve_handler(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    wd_id = query.data.split('_')[2]
    wd = get_withdrawal(wd_id)
    if wd:
        update_withdrawal_status(wd_id, 'paid')
        await bot.send_message(wd[1], f"Your withdrawal #{wd_id} has been approved and processed. Net amount: ${wd[5]:.2f}")
        await query.message.edit_text(query.message.text + "\n✅ Approved")

async def wd_deny_handler(query: types.CallbackQuery):
    from main import bot
    if query.from_user.id not in ADMIN_IDS:
        return
    wd_id = query.data.split('_')[2]
    wd = get_withdrawal(wd_id)
    if wd:
        update_withdrawal_status(wd_id, 'denied', 'Denied by admin')
        update_balance(wd[1], wd[3])  # Refund amount
        await bot.send_message(wd[1], f"Your withdrawal #{wd_id} was denied. Amount ${wd[3]:.2f} refunded to your balance.")
        await query.message.edit_text(query.message.text + "\n❌ Denied")