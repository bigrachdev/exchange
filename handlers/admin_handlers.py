# handlers/admin_handlers.py - Complete admin panel with smooth navigation

import logging
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, ADMIN_CHANNEL_ID
from database import (
    get_all_users, get_all_transactions, update_transaction_status, 
    update_balance, reward_exists, add_reward, update_reward_status,
    get_reward, get_withdrawal, update_withdrawal_status, get_pending_withdrawals,
    get_transaction, get_referred_by, get_user, get_available_code
)
from utils import format_currency, truncate_text

def register_admin_handlers(dp: Dispatcher):
    # Admin command handlers
    dp.register_message_handler(admin_panel, commands=['admin'], user_id=ADMIN_IDS, state='*')
    dp.register_message_handler(stats_command, commands=['stats'], user_id=ADMIN_IDS)
    dp.register_message_handler(broadcast_command, commands=['broadcast'], user_id=ADMIN_IDS)
    
    # Transaction handlers
    dp.register_callback_query_handler(admin_valid, lambda c: c.data.startswith('admin_valid_'))
    dp.register_callback_query_handler(admin_invalid, lambda c: c.data.startswith('admin_invalid_'))
    dp.register_callback_query_handler(complete_buy_tx, lambda c: c.data.startswith('complete_tx_'))
    dp.register_callback_query_handler(admin_invalid_payment, lambda c: c.data.startswith('admin_invalid_payment_'))
    
    # Reward handlers
    dp.register_callback_query_handler(reward_paid_handler, lambda c: c.data.startswith('reward_paid_'))
    
    # Withdrawal handlers
    dp.register_callback_query_handler(wd_approve_handler, lambda c: c.data.startswith('wd_approve_'))
    dp.register_callback_query_handler(wd_deny_handler, lambda c: c.data.startswith('wd_deny_'))
    
    # Admin panel navigation
    dp.register_callback_query_handler(admin_transactions, lambda c: c.data == 'admin_transactions')
    dp.register_callback_query_handler(admin_withdrawals, lambda c: c.data == 'admin_withdrawals')
    dp.register_callback_query_handler(admin_users, lambda c: c.data == 'admin_users')
    dp.register_callback_query_handler(admin_analytics, lambda c: c.data == 'admin_analytics')
    dp.register_callback_query_handler(back_to_admin_panel, lambda c: c.data == 'admin_panel')

async def admin_panel(message: types.Message | types.CallbackQuery, state: FSMContext = None):
    """Show admin panel with refresh functionality"""
    if isinstance(message, types.CallbackQuery):
        user_id = message.from_user.id
        chat_message = message.message
        await message.answer()
    else:
        user_id = message.from_user.id
        chat_message = message
    
    if user_id not in ADMIN_IDS:
        return
    
    if state:
        await state.finish()
    
    # Get statistics
    users = get_all_users()
    pending_tx = get_all_transactions('pending')
    pending_wd = get_pending_withdrawals()
    
    total_balance = sum(user[2] for user in users)
    
    text = f"""
👑 ADMIN PANEL

📊 Live Statistics:
• Total Users: {len(users)}
• Total Balance: {format_currency(total_balance)}
• Pending Transactions: {len(pending_tx)}
• Pending Withdrawals: {len(pending_wd)}

💡 Quick Actions:
"""
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"📊 Transactions ({len(pending_tx)})", callback_data="admin_transactions"),
        InlineKeyboardButton(f"💸 Withdrawals ({len(pending_wd)})", callback_data="admin_withdrawals")
    )
    keyboard.add(
        InlineKeyboardButton("👥 Users List", callback_data="admin_users"),
        InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics")
    )
    keyboard.add(
        InlineKeyboardButton("🔄 Refresh", callback_data="admin_panel")
    )
    
    try:
        await chat_message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await chat_message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def back_to_admin_panel(query: types.CallbackQuery):
    """Handle back to admin panel navigation"""
    await admin_panel(query, None)

async def admin_transactions(query: types.CallbackQuery):
    """Display pending transactions"""
    await query.answer()
    
    pending_tx = get_all_transactions('pending')
    
    if not pending_tx:
        text = "📊 Pending Transactions\n\n✅ No pending transactions at the moment."
    else:
        text = "📊 Pending Transactions\n\n"
        for i, tx in enumerate(pending_tx[:10], 1):  # Limit to 10 to avoid long messages
            tx_id = tx[0]
            user_id = tx[1]
            tx_type = tx[2]
            card = tx[3]
            denom = tx[4]
            calc = tx[5]
            
            text += f"**{i}. {tx_type.upper()}**\n"
            text += f"   ID: `{truncate_text(tx_id, 12)}`\n"
            text += f"   User: `{user_id}`\n"
            text += f"   Card: {card}\n"
            text += f"   Amount: ${denom:.0f} → {format_currency(calc)}\n"
            text += f"   [Manage in Admin Channel](#)\n\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_panel"))
    keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_transactions"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_withdrawals(query: types.CallbackQuery):
    """Display pending withdrawals"""
    await query.answer()
    
    pending_wd = get_pending_withdrawals()
    
    if not pending_wd:
        text = "💸 Pending Withdrawals\n\n✅ No pending withdrawals at the moment."
    else:
        text = "💸 Pending Withdrawals\n\n"
        for i, wd in enumerate(pending_wd[:10], 1):
            wd_id = wd[0]
            user_id = wd[1]
            method = wd[2]
            amount = wd[3]
            net = wd[5]
            details = wd[6]
            
            method_emoji = "🔗" if method == "crypto" else "🏦"
            text += f"**{i}. {method_emoji} {method.upper()}**\n"
            text += f"   ID: `{truncate_text(wd_id, 12)}`\n"
            text += f"   User: `{user_id}`\n"
            text += f"   Amount: {format_currency(amount)}\n"
            text += f"   Net: {format_currency(net)}\n"
            text += f"   Details: {truncate_text(details, 30)}\n"
            text += f"   [Manage in Admin Channel](#)\n\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_panel"))
    keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_withdrawals"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_users(query: types.CallbackQuery):
    """Display users list"""
    await query.answer()
    
    users = get_all_users()
    
    if not users:
        text = "👥 Users List\n\n❌ No users registered yet."
    else:
        total_balance = sum(user[2] for user in users)
        avg_balance = total_balance / len(users) if users else 0
        
        text = f"👥 Users List\n\n"
        text += f"**Summary:**\n"
        text += f"• Total Users: {len(users)}\n"
        text += f"• Total Balance: {format_currency(total_balance)}\n"
        text += f"• Average Balance: {format_currency(avg_balance)}\n\n"
        
        text += "**Recent Users (Last 10):**\n"
        for user in users[:10]:
            user_id = user[0]
            username = user[1] or "No Username"
            balance = user[2]
            joined = user[4] or "Unknown"
            
            text += f"`{user_id}` | @{username} | {format_currency(balance)}\n"
        
        if len(users) > 10:
            text += f"\n... and {len(users) - 10} more users"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_panel"))
    keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_users"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_analytics(query: types.CallbackQuery):
    """Display analytics overview"""
    await query.answer()
    
    users = get_all_users()
    all_tx = get_all_transactions()
    
    completed_tx = [tx for tx in all_tx if tx[6] == 'completed']
    pending_tx = [tx for tx in all_tx if tx[6] == 'pending']
    failed_tx = [tx for tx in all_tx if tx[6] == 'failed']
    
    sell_tx = [tx for tx in completed_tx if tx[2] == 'sell']
    buy_tx = [tx for tx in completed_tx if tx[2] == 'buy']
    
    total_balance = sum(user[2] for user in users)
    total_sell_volume = sum(tx[5] for tx in sell_tx)
    total_buy_volume = sum(tx[5] for tx in buy_tx)
    total_volume = total_sell_volume + total_buy_volume
    
    # Calculate success rate
    success_rate = (len(completed_tx) / len(all_tx)) * 100 if all_tx else 0
    
    text = f"""
📈 Analytics Overview

👥 **Users:**
• Total Users: {len(users)}
• Total Balance: {format_currency(total_balance)}
• Avg Balance: {format_currency(total_balance / len(users) if users else 0)}

📊 **Transactions:**
• Total: {len(all_tx)}
• Completed: {len(completed_tx)}
• Pending: {len(pending_tx)}
• Failed: {len(failed_tx)}
• Success Rate: {success_rate:.1f}%

💰 **Volume:**
• Sell Volume: {format_currency(total_sell_volume)}
• Buy Volume: {format_currency(total_buy_volume)}
• Total Volume: {format_currency(total_volume)}

🔄 **Breakdown:**
• Sell Transactions: {len(sell_tx)}
• Buy Transactions: {len(buy_tx)}
• Avg Sell: {format_currency(total_sell_volume / len(sell_tx)) if sell_tx else '$0'}
• Avg Buy: {format_currency(total_buy_volume / len(buy_tx)) if buy_tx else '$0'}
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_panel"))
    keyboard.add(InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_detailed_stats"))
    keyboard.add(InlineKeyboardButton("🔄 Refresh", callback_data="admin_analytics"))
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def stats_command(message: types.Message):
    """Show detailed statistics via command"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    users = get_all_users()
    all_tx = get_all_transactions()
    
    completed_tx = [tx for tx in all_tx if tx[6] == 'completed']
    pending_tx = [tx for tx in all_tx if tx[6] == 'pending']
    failed_tx = [tx for tx in all_tx if tx[6] == 'failed']
    
    sell_tx = [tx for tx in completed_tx if tx[2] == 'sell']
    buy_tx = [tx for tx in completed_tx if tx[2] == 'buy']
    
    total_balance = sum(user[2] for user in users)
    total_sell_volume = sum(tx[5] for tx in sell_tx)
    total_buy_volume = sum(tx[5] for tx in buy_tx)
    
    text = f"""
📊 DETAILED STATISTICS

👥 Users:
• Total: {len(users)}
• Total Balance: {format_currency(total_balance)}
• Avg Balance: {format_currency(total_balance / len(users) if users else 0)}

📈 Transactions:
• Total: {len(all_tx)}
• Completed: {len(completed_tx)}
• Pending: {len(pending_tx)}
• Failed: {len(failed_tx)}

💰 Volume:
• Sell Volume: {format_currency(total_sell_volume)}
• Buy Volume: {format_currency(total_buy_volume)}
• Total Volume: {format_currency(total_sell_volume + total_buy_volume)}

🔍 Breakdown:
• Sell Transactions: {len(sell_tx)}
• Buy Transactions: {len(buy_tx)}
"""
    
    await message.answer(text, parse_mode="Markdown")

async def broadcast_command(message: types.Message):
    """Broadcast message to all users"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Extract message to broadcast
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Usage: /broadcast <message>")
        return
    
    broadcast_text = parts[1]
    users = get_all_users()
    
    # Confirmation keyboard
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Confirm Broadcast", callback_data=f"confirm_broadcast:{len(users)}:{broadcast_text}"),
        InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")
    )
    
    await message.answer(
        f"📢 Broadcast Confirmation\n\n"
        f"Message: {broadcast_text}\n\n"
        f"Will be sent to: {len(users)} users\n\n"
        f"**Are you sure?**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Transaction approval handlers
async def admin_valid(query: types.CallbackQuery):
    """Approve sell transaction"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("✅ Transaction approved!")
    
    tx_id = query.data.split('_')[-1]
    tx = get_transaction(tx_id)
    
    if not tx:
        await query.message.edit_text(query.message.text + "\n\n❌ Transaction not found")
        return
    
    user_id = tx[1]
    tx_type = tx[2]
    calculated = tx[5]
    
    if tx_type == 'sell':
        # Update transaction
        update_transaction_status(tx_id, 'completed')
        
        # Add balance
        update_balance(user_id, calculated, add=True)
        
        # Notify user
        await bot.send_message(
            user_id,
            f"✅ Sale Approved!\n\n"
            f"Transaction ID: `{tx_id}`\n"
            f"Amount: {format_currency(calculated)}\n\n"
            f"Your balance has been credited!",
            parse_mode="Markdown"
        )
        
        # Update admin message
        await query.message.edit_text(
            query.message.text + "\n\n✅ APPROVED - Balance updated",
            parse_mode="Markdown"
        )
        
        # Trigger referral reward
        await trigger_referral_reward(tx_id, query.message)

async def admin_invalid(query: types.CallbackQuery):
    """Reject transaction"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("❌ Transaction rejected!")
    
    tx_id = query.data.split('_')[-1]
    tx = get_transaction(tx_id)
    
    if not tx:
        await query.message.edit_text(query.message.text + "\n\n❌ Transaction not found")
        return
    
    update_transaction_status(tx_id, 'failed', 'Invalid card')
    
    await bot.send_message(
        tx[1],
        f"❌ Sale Rejected\n\nTransaction ID: `{tx_id}`\nReason: Invalid card\n\nPlease try again with a valid card.",
        parse_mode="Markdown"
    )
    
    await query.message.edit_text(
        query.message.text + "\n\n❌ REJECTED - User notified",
        parse_mode="Markdown"
    )

async def admin_invalid_payment(query: types.CallbackQuery):
    """Handle invalid payment for buy transactions"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("❌ Payment marked as invalid!")
    
    tx_id = query.data.split('_')[-1]
    tx = get_transaction(tx_id)
    
    if not tx:
        await query.message.edit_text(query.message.text + "\n\n❌ Transaction not found")
        return
    
    # Update transaction status
    update_transaction_status(tx_id, 'failed', 'Invalid payment')
    
    # Notify user
    await bot.send_message(
        tx[1],
        f"❌ Payment Verification Failed\n\n"
        f"Transaction ID: `{tx_id}`\n"
        f"Reason: Invalid payment or transaction hash\n\n"
        f"Please check your payment details and try again. Contact support if you believe this is an error: @SupportHandle",
        parse_mode="Markdown"
    )
    
    # Update admin message
    await query.message.edit_text(
        query.message.text + "\n\n❌ PAYMENT INVALID - User notified",
        parse_mode="Markdown"
    )

async def complete_buy_tx(query: types.CallbackQuery):
    """Complete buy transaction by sending code"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("✅ Purchase completed!")
    
    tx_id = query.data.split('_')[-1]
    tx = get_transaction(tx_id)
    
    if not tx or tx[2] != 'buy':
        await query.message.edit_text(query.message.text + "\n\n❌ Invalid buy transaction")
        return
    
    user_id = tx[1]
    card_name = tx[3]
    denomination = tx[4]
    
    # Get code from inventory
    code = get_available_code(card_name, denomination)
    
    if code:
        # Update transaction
        update_transaction_status(tx_id, 'completed')
        
        # Send code to user
        await bot.send_message(
            user_id,
            f"✅ Purchase Complete!\n\n"
            f"Transaction ID: `{tx_id}`\n"
            f"Card: {card_name}\n"
            f"Denomination: ${denomination:.0f}\n\n"
            f"Your Gift Card Code:\n`{code}`\n\n"
            f"Enjoy your purchase! 🎉",
            parse_mode="Markdown"
        )
        
        # Update admin message
        await query.message.edit_text(
            query.message.text + "\n\n✅ DELIVERED - Code sent to user",
            parse_mode="Markdown"
        )
        
        # Trigger referral reward
        await trigger_referral_reward(tx_id, query.message)
    else:
        # Out of stock
        update_transaction_status(tx_id, 'failed', 'Out of stock')
        
        await bot.send_message(
            user_id,
            f"❌ Purchase Failed\n\n"
            f"Transaction ID: `{tx_id}`\n"
            f"Reason: Out of stock\n\n"
            f"Refund will be processed shortly. Please contact support: @SupportHandle",
            parse_mode="Markdown"
        )
        
        await query.message.edit_text(
            query.message.text + "\n\n❌ OUT OF STOCK - Refund needed",
            parse_mode="Markdown"
        )

async def trigger_referral_reward(tx_id, admin_message):
    """Create referral reward if applicable"""
    from main import bot
    
    tx = get_transaction(tx_id)
    if not tx:
        return
    
    user_id = tx[1]
    referred_by = get_referred_by(user_id)
    
    if referred_by and not reward_exists(referred_by, user_id):
        # Create reward
        reward_id = add_reward(referred_by, user_id, tx_id, 5.0)
        
        # Get user info
        referrer = get_user(referred_by)
        referred = get_user(user_id)
        
        # Notify admin
        reward_text = f"""
🎁 NEW REFERRAL REWARD

Reward ID: {reward_id}
Referrer: @{referrer[1] if referrer and referrer[1] else 'Unknown'} (ID: {referred_by})
Referred: @{referred[1] if referred and referred[1] else 'Unknown'} (ID: {user_id})
Amount: $5.00
Related TX: `{tx_id}`

Status: ⏳ Pending Payment
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✅ Mark as Paid", callback_data=f"reward_paid_{reward_id}"))
        
        try:
            await bot.send_message(
                ADMIN_CHANNEL_ID,
                reward_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except:
            pass

async def reward_paid_handler(query: types.CallbackQuery):
    """Mark referral reward as paid"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("✅ Reward marked as paid!")
    
    reward_id = int(query.data.split('_')[-1])
    reward = get_reward(reward_id)
    
    if not reward:
        await query.message.edit_text(query.message.text + "\n\n❌ Reward not found")
        return
    
    referrer_id = reward[1]
    amount = reward[3]
    
    # Update reward status
    update_reward_status(reward_id, 'paid')
    
    # Add to referrer balance
    update_balance(referrer_id, amount, add=True)
    
    # Notify referrer
    await bot.send_message(
        referrer_id,
        f"🎉 Referral Reward Paid!\n\n"
        f"You've earned {format_currency(amount)} for referring a friend!\n\n"
        f"Your balance has been credited. Keep sharing and earning!",
        parse_mode="Markdown"
    )
    
    # Update admin message
    await query.message.edit_text(
        query.message.text + "\n\n✅ PAID - Balance updated",
        parse_mode="Markdown"
    )

async def wd_approve_handler(query: types.CallbackQuery):
    """Approve withdrawal"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("✅ Withdrawal approved!")
    
    wd_id = query.data.split('_')[-1]
    wd = get_withdrawal(wd_id)
    
    if not wd:
        await query.message.edit_text(query.message.text + "\n\n❌ Withdrawal not found")
        return
    
    user_id = wd[1]
    net_amount = wd[5]
    
    # Update status
    update_withdrawal_status(wd_id, 'paid')
    
    # Notify user
    await bot.send_message(
        user_id,
        f"✅ Withdrawal Approved!\n\n"
        f"Withdrawal ID: `{wd_id}`\n"
        f"Amount: {format_currency(net_amount)}\n\n"
        f"Your funds have been processed and should arrive within 24-48 hours.",
        parse_mode="Markdown"
    )
    
    # Update admin message
    await query.message.edit_text(
        query.message.text + "\n\n✅ APPROVED - Funds processed",
        parse_mode="Markdown"
    )

async def wd_deny_handler(query: types.CallbackQuery):
    """Deny withdrawal and refund"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer("❌ Withdrawal denied!")
    
    wd_id = query.data.split('_')[-1]
    wd = get_withdrawal(wd_id)
    
    if not wd:
        await query.message.edit_text(query.message.text + "\n\n❌ Withdrawal not found")
        return
    
    user_id = wd[1]
    amount = wd[3]
    
    # Update status
    update_withdrawal_status(wd_id, 'denied', 'Denied by admin')
    
    # Refund balance
    update_balance(user_id, amount, add=True)
    
    # Notify user
    await bot.send_message(
        user_id,
        f"❌ Withdrawal Denied\n\n"
        f"Withdrawal ID: `{wd_id}`\n"
        f"Amount: {format_currency(amount)}\n\n"
        f"Your funds have been refunded to your balance. Please contact support for more information: @SupportHandle",
        parse_mode="Markdown"
    )
    
    # Update admin message
    await query.message.edit_text(
        query.message.text + "\n\n❌ DENIED - Amount refunded",
        parse_mode="Markdown"
    )