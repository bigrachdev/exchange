# handlers/main_handlers.py - Enhanced main menu with dashboard

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (add_user, get_user_by_referral_code, get_referral_code, 
                     get_user_stats, get_user_transactions, get_trending_cards,
                     update_last_activity)
from config import BOT_USERNAME
from utils import create_back_button, format_currency, format_transaction_status

def register_main_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=['start'], state='*')
    dp.register_callback_query_handler(show_main_menu, lambda c: c.data == 'main_menu', state='*')
    dp.register_callback_query_handler(cancel_handler, lambda c: c.data == 'cancel_action', state='*')
    dp.register_callback_query_handler(rates_handler, lambda c: c.data == 'rates')
    dp.register_callback_query_handler(transactions_handler, lambda c: c.data == 'transactions')
    dp.register_callback_query_handler(help_handler, lambda c: c.data == 'help')
    dp.register_callback_query_handler(refer_earn_handler, lambda c: c.data == 'refer_earn')
    dp.register_callback_query_handler(balance_withdraw_handler, lambda c: c.data == 'balance_withdraw')

async def start_handler(message: types.Message, state: FSMContext):
    """Handle /start command with referral support"""
    # Clear any existing state
    await state.finish()
    
    payload = None
    if len(message.text.split()) > 1:
        payload = message.text.split(maxsplit=1)[1]
    
    referred_by = None
    if payload:
        referrer = get_user_by_referral_code(payload)
        if referrer:
            referred_by = referrer[0]
            await message.answer(
                f"🎉 Welcome! You were referred by @{referrer[1] or 'User'}!\n"
                f"Complete your first transaction and you both earn $5! 💰"
            )
    
    add_user(message.from_user.id, message.from_user.username, referred_by)
    update_last_activity(message.from_user.id)
    await show_main_menu(message, state)

async def show_main_menu(message: types.Message | types.CallbackQuery, state: FSMContext = None):
    """Display enhanced dashboard with user stats"""
    if state:
        await state.finish()
    
    if isinstance(message, types.CallbackQuery):
        await message.answer()
        user_id = message.from_user.id
        chat_message = message.message
    else:
        user_id = message.from_user.id
        chat_message = message
    
    update_last_activity(user_id)
    
    # Get user statistics
    stats = get_user_stats(user_id)
    
    # Get trending cards
    trending = get_trending_cards(5)
    trending_text = ""
    if trending:
        trending_text = "\n\n🔥 Trending Cards:\n" + "\n".join([
            f"  {i+1}. {card[0]} ({card[1]} sales)" 
            for i, card in enumerate(trending)
        ])
    
    # Create dashboard text
    dashboard = f"""
🏦 TOPO EXCHANGE Dashboard

👤 User: @{stats['username'] or 'Unknown'}
💰 Balance: {format_currency(stats['balance'])}
📊 Transactions: {stats['transactions']} completed
👥 Referrals: {stats['referrals']} users{trending_text}

Choose an option below:
"""
    
    # Create main menu keyboard
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛒 Sell Gift Card", callback_data="sell_start"),
        InlineKeyboardButton("💳 Buy Gift Card", callback_data="buy_start")
    )
    keyboard.add(
        InlineKeyboardButton("📈 View Rates", callback_data="rates"),
        InlineKeyboardButton("📜 My Transactions", callback_data="transactions")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Balance & Withdraw", callback_data="balance_withdraw"),
        InlineKeyboardButton("👥 Refer & Earn $5", callback_data="refer_earn")
    )
    keyboard.add(
        InlineKeyboardButton("🆘 Help & Support", callback_data="help")
    )
    
    try:
        await chat_message.edit_text(dashboard, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await chat_message.answer(dashboard, reply_markup=keyboard, parse_mode="Markdown")

async def cancel_handler(query: types.CallbackQuery, state: FSMContext):
    """Handle cancel button - return to main menu"""
    await query.answer("❌ Action cancelled")
    await state.finish()
    await show_main_menu(query, state)

async def rates_handler(query: types.CallbackQuery):
    """Display current rates"""
    await query.answer()
    
    text = """
📈 Current Rates

Our rates vary by gift card and market conditions.

Sell Rates: 5% - 25% discount
Buy Rates: 10% - 30% premium

💡 Tip: Rates are calculated dynamically when you select a card.

Popular cards usually have better rates!
"""
    
    await query.message.edit_text(text, reply_markup=create_back_button(), parse_mode="Markdown")

async def transactions_handler(query: types.CallbackQuery):
    """Display user transaction history"""
    await query.answer()
    
    transactions = get_user_transactions(query.from_user.id, limit=10)
    
    if not transactions:
        text = "📜 Transaction History\n\nNo transactions yet. Start trading to see your history!"
    else:
        text = "📜 Transaction History (Last 10)\n\n"
        for tx in transactions:
            tx_type = "🛒 Sell" if tx[1] == 'sell' else "💳 Buy"
            status = format_transaction_status(tx[5])
            text += f"{tx[0]}\n"
            text += f"{tx_type} {tx[2]} ${tx[3]:.0f} → {format_currency(tx[4])}\n"
            text += f"Status: {status}\n"
            text += f"Date: {tx[6][:16]}\n\n"
    
    await query.message.edit_text(text, reply_markup=create_back_button(), parse_mode="Markdown")

async def help_handler(query: types.CallbackQuery):
    """Display help information"""
    await query.answer()
    
    text = """
🆘 Help & Support

How to Sell:
1. Click "🛒 Sell Gift Card"
2. Select your gift card
3. Enter the amount
4. Upload photo or code
5. Wait for verification

How to Buy:
1. Click "💳 Buy Gift Card"
2. Select gift card
3. Enter amount
4. Pay with crypto
5. Receive your code

Withdrawals:
- Minimum: $30 (Crypto) or $100 (Bank)
- Crypto: No fees
- Bank: 7% fee

Referrals:
- Earn $5 per referral
- Your friend earns $5 too
- Unlimited earnings!

Need Help?
Contact support: @SupportHandle

Available 24/7 🕐
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💬 Contact Support", url="https://t.me/SupportHandle"))
    keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def refer_earn_handler(query: types.CallbackQuery):
    """Display referral information"""
    await query.answer()
    
    from database import get_referrals_count, get_pending_rewards_amount, get_paid_rewards_amount
    
    code = get_referral_code(query.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start={code}"
    count = get_referrals_count(query.from_user.id)
    pending = get_pending_rewards_amount(query.from_user.id)
    paid = get_paid_rewards_amount(query.from_user.id)
    
    text = f"""
👥 Refer & Earn $5

Share your link and earn $5 for each friend who completes their first transaction!

Your Referral Link:
`{link}`

Your Stats:
• Referred Users: {count}
• Pending Rewards: {format_currency(pending)}
• Earned Rewards: {format_currency(paid)}

How it Works:
1. Share your link with friends
2. They sign up and complete first transaction
3. You both get $5 credited!

💡 Tip: Share on social media for more referrals!
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={link}&text=Join TOPO EXCHANGE and get $5 bonus!"))
    keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def balance_withdraw_handler(query: types.CallbackQuery):
    """Display balance and withdrawal options"""
    await query.answer()
    
    from database import get_referrals_count, get_pending_rewards_amount, get_paid_rewards_amount, get_user_withdrawals
    
    balance = get_user_stats(query.from_user.id)['balance']
    referrals = get_referrals_count(query.from_user.id)
    pending_rewards = get_pending_rewards_amount(query.from_user.id)
    paid_rewards = get_paid_rewards_amount(query.from_user.id)
    withdrawals = get_user_withdrawals(query.from_user.id)
    
    wd_text = ""
    if withdrawals:
        wd_text = "\n\nRecent Withdrawals:\n"
        for wd in withdrawals[:3]:
            status_emoji = "✅" if wd[3] == "paid" else "⏳" if wd[3] == "pending" else "❌"
            wd_text += f"{status_emoji} {wd[0]}: {format_currency(wd[2])} via {wd[1]}\n"
    
    text = f"""
💰 Balance & Withdrawals

Current Balance: {format_currency(balance)}

Referral Stats:
• Active Referrals: {referrals}
• Pending Rewards: {format_currency(pending_rewards)}
• Total Earned: {format_currency(paid_rewards)}{wd_text}

Withdrawal Options:
🏦 Bank Transfer: $100 min (7% fee)
🔗 Crypto (USDT): $30 min (No fee)
"""
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    if balance >= 30:
        keyboard.add(InlineKeyboardButton("💸 Withdraw Funds", callback_data="withdraw_start"))
    else:
        keyboard.add(InlineKeyboardButton("⚠️ Insufficient Balance ($30 min)", callback_data="insufficient"))
    keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")