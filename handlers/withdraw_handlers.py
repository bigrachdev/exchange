# handlers/withdraw_handlers.py - Handlers for withdrawal flow

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup  # type: ignore
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHANNEL_ID
from database import get_balance, update_balance, add_withdrawal
import uuid

class WithdrawStates(StatesGroup):
    method = State()
    amount = State()
    details = State()

def register_withdraw_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(withdraw_start, lambda c: c.data == 'withdraw_start')
    dp.register_callback_query_handler(choose_method, lambda c: c.data.startswith('wd_'), state=WithdrawStates.method)
    dp.register_message_handler(enter_amount, state=WithdrawStates.amount)
    dp.register_message_handler(enter_details, state=WithdrawStates.details)

async def withdraw_start(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    balance = get_balance(query.from_user.id)
    if balance < 30:
        await query.message.answer("Your balance is too low. Minimum for crypto is $30.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🏦 Bank Transfer ($100 min, 7% fee)", callback_data="wd_bank"),
        InlineKeyboardButton("🔗 Crypto (USDT, $30 min, no fee)", callback_data="wd_crypto")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="balance_withdraw"))
    await query.message.answer("Select withdrawal method:", reply_markup=keyboard)
    await WithdrawStates.method.set()

async def choose_method(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    method = query.data.split('_')[1]
    min_amount = 100 if method == 'bank' else 30
    fee_pct = 7 if method == 'bank' else 0
    await state.update_data(method=method, min_amount=min_amount, fee_pct=fee_pct)
    await query.message.answer(f"Enter amount to withdraw (min ${min_amount}):")
    await WithdrawStates.amount.set()

async def enter_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        amount = float(message.text)
        if amount < data['min_amount']:
            raise ValueError("Amount below minimum.")
        balance = get_balance(message.from_user.id)
        if amount > balance:
            raise ValueError("Insufficient balance.")
        fee = amount * (data['fee_pct'] / 100)
        net_amount = amount - fee
        await state.update_data(amount=amount, fee=fee, net_amount=net_amount)
        details_prompt = "Enter your bank account details:" if data['method'] == 'bank' else "Enter your USDT wallet address:"
        await message.answer(details_prompt + "\nNeed help? @SupportHandle | ⬅️ Back")
        await WithdrawStates.details.set()
    except ValueError as e:
        await message.answer(str(e) + " Please try again.")

async def enter_details(message: types.Message, state: FSMContext):
    from main import bot
    details = message.text
    data = await state.get_data()
    wd_id = f"WD{uuid.uuid4().hex[:8].upper()}"
    update_balance(message.from_user.id, data['amount'], add=False)  # Deduct amount
    add_withdrawal(wd_id, message.from_user.id, data['method'], data['amount'], data['fee'], data['net_amount'], details)
    await message.answer(f"Withdrawal request #{wd_id} created. Awaiting admin approval.\nNeed help? @SupportHandle")
    # Notify admin
    admin_text = (
        f"New Withdrawal Request\n"
        f"User ID: {message.from_user.id} @{message.from_user.username}\n"
        f"WD ID: {wd_id}\n"
        f"Method: {data['method']}\n"
        f"Amount: ${data['amount']:.2f}\n"
        f"Fee: ${data['fee']:.2f}\n"
        f"Net: ${data['net_amount']:.2f}\n"
        f"Details: {details}"
    )
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{wd_id}"),
        InlineKeyboardButton("❌ Deny", callback_data=f"wd_deny_{wd_id}")
    )
    await bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_keyboard)
    await state.finish()