# handlers/withdraw_handlers.py - Enhanced withdrawal flow

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHANNEL_ID
from database import get_balance, update_balance, add_withdrawal, update_last_activity
from utils import create_cancel_button, create_confirmation_keyboard, format_currency
import uuid

class WithdrawStates(StatesGroup):
    method = State()
    amount = State()
    details = State()
    confirm = State()

def register_withdraw_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(withdraw_start, lambda c: c.data == 'withdraw_start', state='*')
    dp.register_callback_query_handler(select_method, lambda c: c.data.startswith('wd_method_'), state=WithdrawStates.method)
    dp.register_message_handler(enter_amount, state=WithdrawStates.amount)
    dp.register_message_handler(enter_details, state=WithdrawStates.details)
    dp.register_callback_query_handler(confirm_withdrawal, lambda c: c.data == 'confirm_wd', state=WithdrawStates.confirm)

async def withdraw_start(query: types.CallbackQuery, state: FSMContext):
    """Start withdrawal flow"""
    await query.answer()
    update_last_activity(query.from_user.id)
    
    balance = get_balance(query.from_user.id)
    
    if balance < 30:
        text = f"""
⚠️ Insufficient Balance

Your current balance: {format_currency(balance)}

Minimum withdrawal amounts:
• Crypto (USDT): $30
• Bank Transfer: $100

Keep trading to increase your balance!
"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu"))
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    text = f"""
💸 Withdraw Funds

Step 1/4: Select Method

Your Balance: {format_currency(balance)}

Choose your withdrawal method:
"""
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if balance >= 30:
        keyboard.add(InlineKeyboardButton(
            "🔗 Crypto (USDT) - $30 min, No Fees ✓",
            callback_data="wd_method_crypto"
        ))
    
    if balance >= 100:
        keyboard.add(InlineKeyboardButton(
            "🏦 Bank Transfer - $100 min, 7% Fee",
            callback_data="wd_method_bank"
        ))
    
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="balance_withdraw"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await WithdrawStates.method.set()

async def select_method(query: types.CallbackQuery, state: FSMContext):
    """Handle method selection"""
    await query.answer()
    
    method = query.data.split('_')[-1]  # crypto or bank
    
    if method == 'crypto':
        min_amount = 30
        fee_pct = 0
        fee_text = "No fees!"
    else:
        min_amount = 100
        fee_pct = 7
        fee_text = "7% processing fee"
    
    await state.update_data(method=method, min_amount=min_amount, fee_pct=fee_pct)
    
    balance = get_balance(query.from_user.id)
    
    text = f"""
💸 Withdraw Funds

Step 2/4: Enter Amount

Method: {'🔗 Crypto (USDT)' if method == 'crypto' else '🏦 Bank Transfer'}
Your Balance: {format_currency(balance)}

Fee: {fee_text}
Minimum: ${min_amount}
Maximum: {format_currency(balance)}

💡 Enter withdrawal amount:
"""
    
    await query.message.edit_text(text, reply_markup=create_cancel_button(), parse_mode="Markdown")
    await WithdrawStates.amount.set()

async def enter_amount(message: types.Message, state: FSMContext):
    """Handle amount input"""
    update_last_activity(message.from_user.id)
    
    try:
        amount = float(message.text)
        data = await state.get_data()
        balance = get_balance(message.from_user.id)
        
        if amount < data['min_amount']:
            await message.answer(
                f"⚠️ Minimum withdrawal is ${data['min_amount']}. Please enter a valid amount:",
                reply_markup=create_cancel_button()
            )
            return
        
        if amount > balance:
            await message.answer(
                f"⚠️ Insufficient balance. Your balance: {format_currency(balance)}. Please enter a valid amount:",
                reply_markup=create_cancel_button()
            )
            return
        
        # Calculate fees
        fee = amount * (data['fee_pct'] / 100)
        net_amount = amount - fee
        
        await state.update_data(amount=amount, fee=fee, net_amount=net_amount)
        
        # Ask for details
        if data['method'] == 'crypto':
            prompt = """
💸 Withdraw Funds

Step 3/4: Wallet Address

Method: 🔗 Crypto (USDT TRC20)

💡 Enter your USDT wallet address:

⚠️ Make sure:
• Address is correct (double-check!)
• Network is TRC20
• You control this wallet

Type or paste your wallet address:
"""
        else:
            prompt = """
💸 Withdraw Funds

Step 3/4: Bank Details

Method: 🏦 Bank Transfer

💡 Enter your bank details:

Format:
```
Bank Name: [Your Bank]
Account Name: [Your Name]
Account Number: [Number]
Routing Number: [If USA]
```

Send all details in one message:
"""
        
        await message.answer(prompt, reply_markup=create_cancel_button(), parse_mode="Markdown")
        await WithdrawStates.details.set()
        
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter numbers only (e.g., 100):", reply_markup=create_cancel_button())

async def enter_details(message: types.Message, state: FSMContext):
    """Handle details input and show confirmation"""
    update_last_activity(message.from_user.id)
    
    details = message.text.strip()
    data = await state.get_data()
    
    if len(details) < 10:
        await message.answer(
            "⚠️ Details seem incomplete. Please provide full information:",
            reply_markup=create_cancel_button()
        )
        return
    
    await state.update_data(details=details)
    
    # Show confirmation
    method_name = "🔗 Crypto (USDT)" if data['method'] == 'crypto' else "🏦 Bank Transfer"
    
    # Truncate details for display
    display_details = details[:100] + "..." if len(details) > 100 else details
    
    text = f"""
✅ Confirm Withdrawal

Step 4/4: Review & Submit

Method: {method_name}
Withdrawal Amount: {format_currency(data['amount'])}
Processing Fee: {format_currency(data['fee'])} ({data['fee_pct']}%)
You'll Receive: {format_currency(data['net_amount'])}

Details:
`{display_details}`

⚠️ Important:
• Funds will be deducted immediately
• Processing takes 24-48 hours
• Make sure all details are correct

Ready to submit?
"""
    
    keyboard = create_confirmation_keyboard("confirm_wd", "cancel_action")
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await WithdrawStates.confirm.set()

async def confirm_withdrawal(query: types.CallbackQuery, state: FSMContext):
    """Process withdrawal request"""
    await query.answer("Processing withdrawal...")
    from main import bot
    
    # Get data
    data = await state.get_data()
    user_id = query.from_user.id
    username = query.from_user.username
    
    # Generate withdrawal ID
    wd_id = f"WD{uuid.uuid4().hex[:8].upper()}"
    
    # Deduct from balance
    update_balance(user_id, data['amount'], add=False)
    
    # Save to database
    add_withdrawal(
        wd_id,
        user_id,
        data['method'],
        data['amount'],
        data['fee'],
        data['net_amount'],
        data['details']
    )
    
    # Notify admin
    method_name = "🔗 Crypto (USDT)" if data['method'] == 'crypto' else "🏦 Bank Transfer"
    
    admin_text = f"""
💸 NEW WITHDRAWAL REQUEST

Withdrawal ID: `{wd_id}`
User: @{username or 'Unknown'} (ID: {user_id})

Method: {method_name}
Amount: {format_currency(data['amount'])}
Fee: {format_currency(data['fee'])}
Net Amount: {format_currency(data['net_amount'])}

Details:
{data['details']}

Status: ⏳ Pending Approval
"""
    
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{wd_id}"),
        InlineKeyboardButton("❌ Deny", callback_data=f"wd_deny_{wd_id}")
    )
    
    try:
        await bot.send_message(
            ADMIN_CHANNEL_ID,
            admin_text,
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending to admin: {e}")
    
    # Notify user
    new_balance = get_balance(user_id)
    
    success_text = f"""
✅ Withdrawal Submitted!

Withdrawal ID: `{wd_id}`
Method: {method_name}
Net Amount: {format_currency(data['net_amount'])}

New Balance: {format_currency(new_balance)}

Status: ⏳ Pending Approval

Your withdrawal is being reviewed by our team. You'll receive a notification once approved.

Processing time: 24-48 hours

Need help? Contact @SupportHandle
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu"))
    
    await query.message.edit_text(success_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Clear state
    await state.finish()
    update_last_activity(user_id)