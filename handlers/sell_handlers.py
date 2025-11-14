# handlers/sell_handlers.py - Handlers for sell flow

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup  # type: ignore
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOP_COUNTRIES, ADMIN_CHANNEL_ID
from database import get_gift_cards, get_random_rate, get_logo_url, add_transaction
import uuid
import asyncio

class SellStates(StatesGroup):
    country = State()
    gift_card = State()
    denomination = State()
    submit_code = State()

def register_sell_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(sell_start, lambda c: c.data == 'sell_start')
    dp.register_callback_query_handler(select_country, lambda c: c.data.startswith('country_'), state=SellStates.country)
    dp.register_callback_query_handler(select_gift_card, lambda c: c.data.startswith('gift_'), state=SellStates.gift_card)
    dp.register_message_handler(enter_denomination, state=SellStates.denomination)
    dp.register_message_handler(submit_code_handler, state=SellStates.submit_code, content_types=['photo', 'text'])

    # Pagination handler defined inside to access dp.storage
    async def page_handler(c: types.CallbackQuery):
        state = FSMContext(storage=dp.storage, chat=c.message.chat.id, user=c.from_user.id)
        await show_gift_cards(c, state, int(c.data.split('_')[2]))

    dp.register_callback_query_handler(page_handler, lambda c: c.data.startswith('sell_page_'), state=SellStates.gift_card)

async def sell_start(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for country in TOP_COUNTRIES:
        keyboard.add(InlineKeyboardButton(f"{country['flag']} {country['name']} ({country['currency']})", callback_data=f"country_{country['name']}"))
    keyboard.add(InlineKeyboardButton("🌍 Other Countries", callback_data="country_other"))
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    await query.message.answer("Select your country to see supported gift cards.", reply_markup=keyboard)
    await SellStates.country.set()

async def select_country(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    country = query.data.split('_')[1] if query.data != 'country_other' else 'Other'  # Handle other countries logic
    await state.update_data(country=country)
    await show_gift_cards(query, state, page=0)

async def show_gift_cards(query: types.CallbackQuery, state: FSMContext, page: int):
    data = await state.get_data()
    country = data.get('country')
    cards = get_gift_cards(country)
    per_page = 5
    start = page * per_page
    end = start + per_page
    keyboard = InlineKeyboardMarkup(row_width=1)
    for card in cards[start:end]:
        keyboard.add(InlineKeyboardButton(card, callback_data=f"gift_{card}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"sell_page_{page-1}"))
    if end < len(cards):
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"sell_page_{page+1}"))
    if nav_buttons:
        keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="sell_start"))
    await query.message.edit_text("Select a gift card to sell.", reply_markup=keyboard)
    await SellStates.gift_card.set()

async def select_gift_card(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    gift_card = query.data.split('_')[1]
    data = await state.get_data()
    country = data.get('country')
    await state.update_data(gift_card=gift_card)
    rate = get_random_rate(gift_card, country)
    common_denoms = [10, 25, 50, 100, 200, 500]
    table = "| Denomination | Discount | You Receive |\n|:-----------|:--------:|:-----------:|\n"
    for d in common_denoms:
        receive = d * (1 - rate / 100)
        table += f"| ${d} | {rate:.1f}% | ${receive:.2f} |\n"
    text = f"**{gift_card}** ({country})\n\n{table}\nEnter the face value (e.g., 100):\n\nNeed help? Contact support: @SupportHandle | ⬅️ Back"
    logo = get_logo_url(gift_card)
    kb = back_keyboard()
    if logo:
        await query.message.answer_photo(logo, caption=text, reply_markup=kb, parse_mode="Markdown")
    else:
        await query.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await SellStates.denomination.set()

async def enter_denomination(message: types.Message, state: FSMContext):
    try:
        denomination = float(message.text)
        data = await state.get_data()
        gift_card = data.get('gift_card')
        country = data.get('country')
        rate = get_random_rate(gift_card, country) / 100
        calculated = denomination * (1 - rate)
        await state.update_data(denomination=denomination, calculated=calculated)
        await message.answer(f"You will receive: ${calculated:.2f}\nPlease send image or code: Need help? @SupportHandle | ⬅️ Back")
        await SellStates.submit_code.set()
    except ValueError:
        await message.answer("Invalid amount. Try again.")

async def submit_code_handler(message: types.Message, state: FSMContext):
    from main import bot
    await message.answer("Verifying your code... ⏳")
    await asyncio.sleep(5)
    tx_id = f"TX{uuid.uuid4().hex[:8].upper()}"
    data = await state.get_data()
    add_transaction(tx_id, message.from_user.id, 'sell', data['gift_card'], data['denomination'], data['calculated'])
    # Forward to admin
    admin_text = f"New Sell: User {message.from_user.id} @{message.from_user.username}\nTX: {tx_id}\nCard: {data['gift_card']} ${data['denomination']}"
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("✅ Valid", callback_data=f"admin_valid_{tx_id}"),
        InlineKeyboardButton("❌ Used", callback_data=f"admin_invalid_used_{tx_id}"),
        InlineKeyboardButton("❌ Invalid", callback_data=f"admin_invalid_code_{tx_id}"),
        InlineKeyboardButton("🔄 Other", callback_data=f"admin_other_{tx_id}")
    )
    if message.photo:
        await bot.send_photo(ADMIN_CHANNEL_ID, message.photo[-1].file_id, caption=admin_text, reply_markup=admin_keyboard)
    else:
        await bot.send_message(ADMIN_CHANNEL_ID, admin_text + f"\nCode: {message.text}", reply_markup=admin_keyboard)
    await message.answer(f"Invoice #{tx_id}. Status: Pending. Need help? @SupportHandle | ⬅️ Back")
    await state.finish()  # Wait for admin action

def back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    return keyboard