# utils.py - Helper functions for navigation and UI

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import GIFT_CARDS, CARDS_PER_PAGE

def create_back_button(callback_data="main_menu"):
    """Create a standard back button"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data=callback_data))
    return keyboard

def create_cancel_button(with_back=False):
    """Create cancel button for input states"""
    keyboard = InlineKeyboardMarkup()
    if with_back:
        keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    else:
        keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
    return keyboard

def paginate_cards(page=0, callback_prefix="card"):
    """Create paginated gift card buttons"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    start = page * CARDS_PER_PAGE
    end = start + CARDS_PER_PAGE
    
    current_cards = GIFT_CARDS[start:end]
    
    # Add gift card buttons (2 per row)
    for card in current_cards:
        keyboard.insert(InlineKeyboardButton(
            card['name'], 
            callback_data=f"{callback_prefix}_{card['name']}"
        ))
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_page_{page-1}"))
    
    # Page indicator
    total_pages = (len(GIFT_CARDS) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
    nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="page_info"))
    
    if end < len(GIFT_CARDS):
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_page_{page+1}"))
    
    keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu"))
    
    return keyboard

def format_currency(amount):
    """Format currency consistently"""
    return f"${amount:.2f}"

def format_rate_table(gift_card_name, rate, is_buy=False):
    """Generate a clean rate table"""
    common_denoms = [10, 25, 50, 100, 200, 500]
    
    if is_buy:
        header = "💳 Buy Rates\n\n"
        rows = []
        for denom in common_denoms:
            pay = denom * (1 + rate / 100)
            rows.append(f"${denom} → You Pay: ${pay:.2f} (+{rate:.1f}%)")
    else:
        header = "💵 Sell Rates\n\n"
        rows = []
        for denom in common_denoms:
            receive = denom * (1 - rate / 100)
            rows.append(f"${denom} → You Get: ${receive:.2f} (-{rate:.1f}%)")
    
    return header + "\n".join(rows)

def create_confirmation_keyboard(confirm_callback, cancel_callback="cancel_action"):
    """Create confirmation keyboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Confirm", callback_data=confirm_callback),
        InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback)
    )
    return keyboard

def format_transaction_status(status):
    """Format transaction status with emoji"""
    status_map = {
        'pending': '⏳ Pending',
        'verified': '🔍 Verifying',
        'completed': '✅ Completed',
        'failed': '❌ Failed'
    }
    return status_map.get(status, status)

def truncate_text(text, max_length=30):
    """Truncate long text for buttons"""
    return text if len(text) <= max_length else text[:max_length-3] + "..."

async def safe_edit_message(message, text, reply_markup=None, parse_mode="Markdown"):
    """Safely edit message, handling errors"""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except Exception as e:
        # If edit fails, send new message
        try:
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except:
            pass
        return False

async def safe_delete_message(message):
    """Safely delete message"""
    try:
        await message.delete()
    except:
        pass