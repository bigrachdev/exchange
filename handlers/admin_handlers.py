# handlers/admin_handlers.py - Enhanced admin panel

import logging
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, ADMIN_CHANNEL_ID
from database import (get_all_users, get_all_transactions, update_transaction_status, 
                     update_balance, reward_exists, add_reward, update_reward_status,
                     get_reward, get_withdrawal, update_withdrawal_status, get_pending_withdrawals,
                     get_transaction, get_referred_by, get_user, get_available_code)
from utils import format_currency

def register_admin_handlers(dp: Dispatcher):
    # Admin command handlers
    dp.register_message_handler(admin_panel, commands=['admin'], user_id=ADMIN_IDS, state='*')
    dp.register_message_handler(stats_command, commands=['stats'], user_id=ADMIN_IDS)
    dp.register_message_handler(broadcast_command, commands=['broadcast'], user_id=ADMIN_IDS)
    
    # Transaction handlers
    dp.register_callback_query_handler(admin_valid, lambda c: c.data.startswith('admin_valid_'))
    dp.register_callback_query_handler(admin_invalid, lambda c: c.data.startswith('admin_invalid_'))
    dp.register_callback_query_handler(complete_buy_tx, lambda c: c.data.startswith('complete_tx_'))
    
    # Reward handlers
    dp.register_callback_query_handler(reward_paid_handler, lambda c: c.data.startswith('reward_paid_'))
    
    # Withdrawal handlers
    dp.register_callback_query_handler(wd_approve_handler, lambda c: c.data.startswith('wd_approve_'))
    dp.register_callback_query_handler(wd_deny_handler, lambda c: c.data.startswith('wd_deny_'))

async def admin_panel(message: types.Message, state: FSMContext):
    """Show admin panel"""
    if message.from_user.id not in ADMIN_IDS:
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

Statistics:
• Total Users: {len(users)}
• Total Balance: {format_currency(total_balance)}
• Pending Transactions: {len(pending_tx)}
• Pending Withdrawals: {len(pending_wd)}

Commands:
/stats - Detailed statistics
/broadcast - Send message to all users

Quick Actions:
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
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def stats_command(message: types.Message):
    """Show detailed statistics"""
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

Users:
• Total: {len(users)}
• Total Balance: {format_currency(total_balance)}
• Avg Balance: {format_currency(total_balance / len(users) if users else 0)}

Transactions:
• Total: {len(all_tx)}
• Completed: {len(completed_tx)}
• Pending: {len(pending_tx)}
• Failed: {len(failed_tx)}

Volume:
• Sell Volume: {format_currency(total_sell_volume)}
• Buy Volume: {format_currency(total_buy_volume)}
• Total Volume: {format_currency(total_sell_volume + total_buy_volume)}

Breakdown:
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
        await message.answer("Usage: /broadcast <message>")
        return
    
    broadcast_text = parts[1]
    users = get_all_users()
    
    success = 0
    failed = 0
    
    from main import bot
    
    for user in users:
        try:
            await bot.send_message(user[0], broadcast_text, parse_mode="Markdown")
            success += 1
        except:
            failed += 1
    
    await message.answer(f"✅ Broadcast sent!\n\nSuccess: {success}\nFailed: {failed}")

# Transaction approval handlers

async def admin_valid(query: types.CallbackQuery):
    """Approve sell transaction"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer()
    
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
    
    await query.answer()
    
    parts = query.data.split('_')
    reason_type = parts[2]
    tx_id = parts[3]
    
    reason_map = {
        'used': 'Code already used',
        'code': 'Invalid or incorrect code',
        'payment': 'Payment not received or invalid',
        'other': 'Issue with submission'
    }
    
    reason = reason_map.get(reason_type, 'Issue with submission')
    
    tx = get_transaction(tx_id)
    if not tx:
        await query.message.edit_text(query.message.text + "\n\n❌ Transaction not found")
        return
    
    # Update transaction
    update_transaction_status(tx_id, 'failed', reason)
    
    # Notify user
    await bot.send_message(
        tx[1],
        f"❌ Transaction Failed\n\n"
        f"Transaction ID: `{tx_id}`\n"
        f"Reason: {reason}\n\n"
        f"Please contact support if you believe this is an error: @SupportHandle",
        parse_mode="Markdown"
    )
    
    # Update admin message
    await query.message.edit_text(
        query.message.text + f"\n\n❌ REJECTED - Reason: {reason}",
        parse_mode="Markdown"
    )

async def complete_buy_tx(query: types.CallbackQuery):
    """Complete buy transaction and deliver code"""
    from main import bot
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    await query.answer()
    
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
        
        # Refund user (if balance was deducted)
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
    
    await query.answer()
    
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
    
    await query.answer()
    
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
    
    await query.answer()
    
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