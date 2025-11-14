# handlers/buy_handlers.py - Handlers for buy flow

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup  # type: ignore
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOP_COUNTRIES, ADMIN_CHANNEL_ID
from database import get_gift_cards, get_random_rate, get_logo_url, add_transaction
import uuid

class BuyStates(StatesGroup):
    country = State()
    gift_card = State()
    denomination = State()
    payment = State()

def register_buy_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(buy_start, lambda c: c.data == 'buy_start')
    dp.register_callback_query_handler(select_country_buy, lambda c: c.data.startswith('country_'), state=BuyStates.country)
    dp.register_callback_query_handler(select_gift_card_buy, lambda c: c.data.startswith('gift_'), state=BuyStates.gift_card)
    dp.register_message_handler(enter_denomination_buy, state=BuyStates.denomination)
    dp.register_message_handler(receive_tx_hash, state=BuyStates.payment)

    # Pagination handler defined inside to access dp.storage
    async def page_handler(c: types.CallbackQuery):
        state = FSMContext(storage=dp.storage, chat=c.message.chat.id, user=c.from_user.id)
        await show_gift_cards_buy(c, state, int(c.data.split('_')[2]))

    dp.register_callback_query_handler(page_handler, lambda c: c.data.startswith('buy_page_'), state=BuyStates.gift_card)

async def buy_start(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for country in TOP_COUNTRIES:
        keyboard.add(InlineKeyboardButton(f"{country['flag']} {country['name']} ({country['currency']})", callback_data=f"country_{country['name']}"))
    keyboard.add(InlineKeyboardButton("🌍 Other Countries", callback_data="country_other"))
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    await query.message.answer("Select country for gift card.", reply_markup=keyboard)
    await BuyStates.country.set()

async def select_country_buy(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    country = query.data.split('_')[1] if query.data != 'country_other' else 'Other'
    await state.update_data(country=country)
    await show_gift_cards_buy(query, state, page=0)

async def show_gift_cards_buy(query: types.CallbackQuery, state: FSMContext, page: int):
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
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"buy_page_{page-1}"))
    if end < len(cards):
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"buy_page_{page+1}"))
    if nav_buttons:
        keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="buy_start"))
    await query.message.edit_text("Select a gift card to buy.", reply_markup=keyboard)
    await BuyStates.gift_card.set()

async def select_gift_card_buy(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    gift_card = query.data.split('_')[1]
    data = await state.get_data()
    country = data.get('country')
    await state.update_data(gift_card=gift_card)
    rate = get_random_rate(gift_card, country, is_buy=True)
    common_denoms = [10, 25, 50, 100, 200, 500]
    table = "| Denomination | Premium | Pay USD |\n|:-----------|:-------:|:-------:|\n"
    for d in common_denoms:
        pay = d * (1 + rate / 100)
        table += f"| ${d} | {rate:.1f}% | ${pay:.2f} |\n"
    text = f"**{gift_card}** ({country})\n\n{table}\nEnter the denomination you wish to buy (e.g., 100):\n\nNeed help? @SupportHandle | ⬅️ Back"
    logo = get_logo_url(gift_card)
    kb = back_keyboard()
    if logo:
        await query.message.answer_photo(logo, caption=text, reply_markup=kb, parse_mode="Markdown")
    else:
        await query.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await BuyStates.denomination.set()

async def enter_denomination_buy(message: types.Message, state: FSMContext):
    try:
        denomination = float(message.text)
        data = await state.get_data()
        gift_card = data['gift_card']
        country = data['country']
        rate = get_random_rate(gift_card, country, is_buy=True) / 100
        calculated = denomination * (1 + rate)
        tx_id = f"TX{uuid.uuid4().hex[:8].upper()}"
        await state.update_data(denomination=denomination, calculated=calculated, tx_id=tx_id)
        add_transaction(tx_id, message.from_user.id, 'buy', gift_card, denomination, calculated)
        payment_address = "bc1q_example_wallet"  # Placeholder
        await message.answer(f"Pay ${calculated:.2f} in crypto to {payment_address}\nSend TX hash after payment: Need help? @SupportHandle | ⬅️ Back")
        await BuyStates.payment.set()
    except ValueError:
        await message.answer("Invalid amount.")

async def receive_tx_hash(message: types.Message, state: FSMContext):
    from main import bot
    data = await state.get_data()
    tx_id = data['tx_id']
    admin_text = f"Buy Payment Proof\nUser {message.from_user.id} @{message.from_user.username}\nTX: {tx_id}\nHash: {message.text}\nAmount: ${data['calculated']:.2f}"
    admin_keyboard = InlineKeyboardMarkup()
    admin_keyboard.add(InlineKeyboardButton("✅ Confirm & Deliver", callback_data=f"complete_tx_{tx_id}"))
    await bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_keyboard)
    await message.answer("TX hash received! Admin will verify shortly.")
    await state.finish()

def back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="main_menu"))
    return keyboard