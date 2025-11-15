# handlers/buy_handlers.py - Enhanced buy flow with smooth navigation

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHANNEL_ID
from database import get_random_rate, get_gift_card_logo, add_transaction, update_last_activity
from utils import paginate_cards, format_rate_table, create_cancel_button, create_confirmation_keyboard, format_currency
import uuid
import asyncio

class BuyStates(StatesGroup):
    select_card = State()
    enter_amount = State()
    payment = State()
    confirm = State()

def register_buy_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(buy_start, lambda c: c.data == 'buy_start', state='*')
    dp.register_callback_query_handler(select_card_page, lambda c: c.data.startswith('buy_page_'), state=BuyStates.select_card)
    dp.register_callback_query_handler(select_card, lambda c: c.data.startswith('buy_') and not c.data.startswith('buy_page_'), state=BuyStates.select_card)
    dp.register_message_handler(enter_amount, state=BuyStates.enter_amount)
    dp.register_message_handler(submit_payment, state=BuyStates.payment)
    dp.register_callback_query_handler(confirm_buy, lambda c: c.data == 'confirm_buy', state=BuyStates.confirm)

async def buy_start(query: types.CallbackQuery, state: FSMContext):
    """Start buy flow - show gift card selection"""
    await query.answer()
    update_last_activity(query.from_user.id)
    
    text = """
💳 Buy Gift Card

Step 1/4: Select Gift Card

Choose the gift card you want to buy from the list below.

💡 All cards are US-based and delivered instantly!
"""
    
    keyboard = paginate_cards(page=0, callback_prefix="buy")
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await BuyStates.select_card.set()

async def select_card_page(query: types.CallbackQuery, state: FSMContext):
    """Handle pagination for card selection"""
    await query.answer()
    page = int(query.data.split('_')[-1])
    
    text = """
💳 Buy Gift Card

Step 1/4: Select Gift Card

Choose the gift card you want to buy from the list below.

💡 All cards are US-based and delivered instantly!
"""
    
    keyboard = paginate_cards(page=page, callback_prefix="buy")
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def select_card(query: types.CallbackQuery, state: FSMContext):
    """Handle gift card selection and show rates"""
    await query.answer()
    
    # Extract card name (remove "buy_" prefix)
    card_name = query.data.replace('buy_', '')
    
    # Get rate for this card
    rate = get_random_rate(card_name, is_buy=True)
    
    # Save to state
    await state.update_data(gift_card=card_name, rate=rate)
    
    # Format rate table
    rate_table = format_rate_table(card_name, rate, is_buy=True)
    
    text = f"""
💳 Buy Gift Card

Step 2/4: Enter Amount

Card: {card_name}

{rate_table}

💡 Example: To buy a $100 card, you pay ${100 * (1 + rate/100):.2f}

Enter the denomination you want to buy (e.g., 100):
"""
    
    # Get logo
    logo = get_gift_card_logo(card_name)
    
    keyboard = create_cancel_button(with_back=True)
    
    # Send with or without logo
    try:
        await query.message.delete()
        if logo:
            await query.message.answer_photo(logo, caption=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await query.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await BuyStates.enter_amount.set()

async def enter_amount(message: types.Message, state: FSMContext):
    """Handle amount input"""
    update_last_activity(message.from_user.id)
    
    try:
        amount = float(message.text)
        
        if amount < 10:
            await message.answer("⚠️ Minimum amount is $10. Please enter a valid amount:", reply_markup=create_cancel_button())
            return
        
        if amount > 10000:
            await message.answer("⚠️ Maximum amount is $10,000. Please enter a valid amount:", reply_markup=create_cancel_button())
            return
        
        # Get data from state
        data = await state.get_data()
        rate = data['rate']
        card_name = data['gift_card']
        
        # Calculate what user needs to pay
        calculated = amount * (1 + rate / 100)
        
        # Save to state
        await state.update_data(denomination=amount, calculated=calculated)
        
        # Payment address (replace with real one)
        payment_address = "TQn4Y7kQgJLmNiMKCVaJ8gN8N5qH9KwXYg"  # Example USDT TRC20
        
        text = f"""
💳 Buy Gift Card

Step 3/4: Payment

Card: {card_name}
Denomination: ${amount:.0f}
Total to Pay: {format_currency(calculated)}
Rate: +{rate:.1f}%

💰 Payment Method: USDT (TRC20)

Send exactly {format_currency(calculated)} USDT to:

`{payment_address}`

⚠️ Important:
• Send only USDT on TRC20 network
• Send exact amount shown above
• Transaction takes 3-10 confirmations

After payment, send your transaction hash:
"""
        
        await message.answer(text, reply_markup=create_cancel_button(), parse_mode="Markdown")
        await BuyStates.payment.set()
        
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter numbers only (e.g., 100):", reply_markup=create_cancel_button())

async def submit_payment(message: types.Message, state: FSMContext):
    """Handle payment hash submission"""
    update_last_activity(message.from_user.id)
    
    tx_hash = message.text.strip()
    
    if len(tx_hash) < 20:
        await message.answer("⚠️ Invalid transaction hash. Please send the complete hash from your wallet:", reply_markup=create_cancel_button())
        return
    
    # Save hash to state
    await state.update_data(tx_hash=tx_hash)
    
    # Get data for confirmation
    data = await state.get_data()
    
    text = f"""
✅ Confirm Your Purchase

Step 4/4: Review & Submit

Card: {data['gift_card']}
Denomination: ${data['denomination']:.0f}
Amount Paid: {format_currency(data['calculated'])}
Rate: +{data['rate']:.1f}%

TX Hash: `{tx_hash[:20]}...`

⚠️ Please confirm:
• You've sent the correct amount
• Transaction hash is correct
• You're ready to complete purchase

Card will be delivered after verification!
"""
    
    keyboard = create_confirmation_keyboard("confirm_buy", "cancel_action")
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await BuyStates.confirm.set()

async def confirm_buy(query: types.CallbackQuery, state: FSMContext):
    """Final confirmation and submission to admin"""
    await query.answer("📤 Processing your purchase...")
    from main import bot
    
    # Show processing message
    processing_msg = await query.message.edit_text(
        "⏳ Processing your purchase...\n\nVerifying payment on blockchain...",
        parse_mode="Markdown"
    )
    
    # Simulate processing
    await asyncio.sleep(2)
    
    # Generate transaction ID
    tx_id = f"TX{uuid.uuid4().hex[:8].upper()}"
    
    # Get all data
    data = await state.get_data()
    user_id = query.from_user.id
    username = query.from_user.username
    
    # Save transaction to database
    add_transaction(
        tx_id, 
        user_id, 
        'buy', 
        data['gift_card'], 
        data['denomination'], 
        data['calculated']
    )
    
    # Prepare admin notification
    admin_text = f"""
💳 NEW PURCHASE REQUEST

Transaction ID: `{tx_id}`
User: @{username or 'Unknown'} (ID: {user_id})

Gift Card: {data['gift_card']}
Denomination: ${data['denomination']:.0f}
Amount Paid: {format_currency(data['calculated'])}
Rate: +{data['rate']:.1f}%

Payment Hash:
`{data['tx_hash']}`

Status: ⏳ Awaiting Verification
"""
    
    # Admin action buttons
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Verify & Deliver", callback_data=f"complete_tx_{tx_id}"),
        InlineKeyboardButton("❌ Invalid Payment", callback_data=f"admin_invalid_payment_{tx_id}")
    )
    
    # Send to admin channel
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
    success_text = f"""
✅ Purchase Submitted Successfully!

Transaction ID: `{tx_id}`
Card: {data['gift_card']}
Denomination: ${data['denomination']:.0f}

Status: ⏳ Verifying Payment

Your payment is being verified on the blockchain. This usually takes 10-30 minutes.

You'll receive your gift card code once payment is confirmed!

Need help? Contact @SupportHandle
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu"))
    keyboard.add(InlineKeyboardButton("📜 View Transactions", callback_data="transactions"))
    
    await processing_msg.edit_text(success_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Clear state
    await state.finish()
    update_last_activity(user_id)