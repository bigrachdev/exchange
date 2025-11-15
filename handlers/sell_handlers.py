# handlers/sell_handlers.py - Enhanced sell flow with smooth navigation

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_CHANNEL_ID
from database import get_random_rate, get_gift_card_logo, add_transaction, update_last_activity
from utils import paginate_cards, format_rate_table, create_cancel_button, create_confirmation_keyboard, format_currency
import uuid
import asyncio

class SellStates(StatesGroup):
    select_card = State()
    enter_amount = State()
    upload_code = State()
    confirm = State()

def register_sell_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(sell_start, lambda c: c.data == 'sell_start', state='*')
    dp.register_callback_query_handler(select_card_page, lambda c: c.data.startswith('sell_page_'), state=SellStates.select_card)
    dp.register_callback_query_handler(select_card, lambda c: c.data.startswith('sell_') and not c.data.startswith('sell_page_'), state=SellStates.select_card)
    dp.register_message_handler(enter_amount, state=SellStates.enter_amount)
    dp.register_message_handler(upload_code, state=SellStates.upload_code, content_types=['photo', 'text'])
    dp.register_callback_query_handler(confirm_sell, lambda c: c.data == 'confirm_sell', state=SellStates.confirm)

async def sell_start(query: types.CallbackQuery, state: FSMContext):
    """Start sell flow - show gift card selection"""
    await query.answer()
    update_last_activity(query.from_user.id)
    
    text = """
🛒 Sell Your Gift Card

Step 1/4: Select Gift Card

Choose the gift card you want to sell from the list below.

💡 All cards are US-based
"""
    
    keyboard = paginate_cards(page=0, callback_prefix="sell")
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await SellStates.select_card.set()

async def select_card_page(query: types.CallbackQuery, state: FSMContext):
    """Handle pagination for card selection"""
    await query.answer()
    page = int(query.data.split('_')[-1])
    
    text = """
🛒 Sell Your Gift Card

Step 1/4: Select Gift Card

Choose the gift card you want to sell from the list below.

💡 All cards are US-based
"""
    
    keyboard = paginate_cards(page=page, callback_prefix="sell")
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def select_card(query: types.CallbackQuery, state: FSMContext):
    """Handle gift card selection and show rates"""
    await query.answer()
    
    # Extract card name (remove "sell_" prefix)
    card_name = query.data.replace('sell_', '')
    
    # Get rate for this card
    rate = get_random_rate(card_name, is_buy=False)
    
    # Save to state
    await state.update_data(gift_card=card_name, rate=rate)
    
    # Format rate table
    rate_table = format_rate_table(card_name, rate, is_buy=False)
    
    text = f"""
🛒 Sell Your Gift Card

Step 2/4: Enter Amount

Card: {card_name}

{rate_table}

💡 Example: If you have a $100 card, you'll receive ${100 * (1 - rate/100):.2f}

Enter the face value of your card (e.g., 100):
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
    
    await SellStates.enter_amount.set()

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
        
        # Calculate what user will receive
        calculated = amount * (1 - rate / 100)
        
        # Save to state
        await state.update_data(denomination=amount, calculated=calculated)
        
        text = f"""
🛒 Sell Your Gift Card

Step 3/4: Upload Card

Card: {card_name}
Face Value: ${amount:.0f}
You'll Receive: {format_currency(calculated)}
Rate: -{rate:.1f}%

📸 Now upload your gift card:
• Send a clear photo of the card (front & back)
• Or type/paste the card code

💡 Make sure all details are visible and readable!
"""
        
        await message.answer(text, reply_markup=create_cancel_button(), parse_mode="Markdown")
        await SellStates.upload_code.set()
        
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter numbers only (e.g., 100):", reply_markup=create_cancel_button())

async def upload_code(message: types.Message, state: FSMContext):
    """Handle code/photo upload and show confirmation"""
    update_last_activity(message.from_user.id)
    
    # Save photo or text to state
    if message.photo:
        await state.update_data(photo_id=message.photo[-1].file_id, code_text=None)
        upload_type = "📸 Photo uploaded"
    else:
        await state.update_data(code_text=message.text, photo_id=None)
        upload_type = "💬 Code received"
    
    # Get data for confirmation
    data = await state.get_data()
    
    text = f"""
✅ Confirm Your Sale

Step 4/4: Review & Submit

Card: {data['gift_card']}
Face Value: ${data['denomination']:.0f}
You'll Receive: {format_currency(data['calculated'])}
Rate: -{data['rate']:.1f}%

{upload_type} ✓

⚠️ Please confirm:
• Your card details are correct
• The card is unused and valid
• You understand submission is final

Ready to submit?
"""
    
    keyboard = create_confirmation_keyboard("confirm_sell", "cancel_action")
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await SellStates.confirm.set()

async def confirm_sell(query: types.CallbackQuery, state: FSMContext):
    """Final confirmation and submission to admin"""
    await query.answer("📤 Submitting your sale...")
    from main import bot
    
    # Show processing message
    processing_msg = await query.message.edit_text(
        "⏳ Processing your sale...\n\nPlease wait while we verify your card.",
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
        'sell', 
        data['gift_card'], 
        data['denomination'], 
        data['calculated']
    )
    
    # Prepare admin notification
    admin_text = f"""
🛒 NEW SALE REQUEST

Transaction ID: `{tx_id}`
User: @{username or 'Unknown'} (ID: {user_id})

Gift Card: {data['gift_card']}
Face Value: ${data['denomination']:.0f}
Payout: {format_currency(data['calculated'])}
Rate: -{data['rate']:.1f}%

Status: ⏳ Awaiting Verification
"""
    
    # Admin action buttons
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Valid", callback_data=f"admin_valid_{tx_id}"),
        InlineKeyboardButton("❌ Used Code", callback_data=f"admin_invalid_used_{tx_id}"),
    )
    admin_keyboard.add(
        InlineKeyboardButton("⚠️ Invalid Code", callback_data=f"admin_invalid_code_{tx_id}"),
        InlineKeyboardButton("🔄 Other Issue", callback_data=f"admin_invalid_other_{tx_id}")
    )
    
    # Send to admin channel with photo or text
    try:
        if data.get('photo_id'):
            await bot.send_photo(
                ADMIN_CHANNEL_ID,
                data['photo_id'],
                caption=admin_text,
                reply_markup=admin_keyboard,
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(
                ADMIN_CHANNEL_ID,
                admin_text + f"\n\nCode:\n`{data['code_text']}`",
                reply_markup=admin_keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Error sending to admin: {e}")
    
    # Notify user
    success_text = f"""
✅ Sale Submitted Successfully!

Transaction ID: `{tx_id}`
Card: {data['gift_card']}
Amount: {format_currency(data['calculated'])}

Status: ⏳ Pending Verification

Your card is being verified by our team. This usually takes 5-15 minutes.

You'll receive a notification once verified and funds will be added to your balance.

Need help? Contact @SupportHandle
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu"))
    keyboard.add(InlineKeyboardButton("📜 View Transactions", callback_data="transactions"))
    
    await processing_msg.edit_text(success_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Clear state
    await state.finish()
    update_last_activity(user_id)