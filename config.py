# config.py - Configuration file for bot settings

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
ADMIN_CHANNEL_ID = int(os.getenv('ADMIN_CHANNEL_ID'))
DB_NAME = os.getenv('DB_NAME', 'bot.db')

BOT_USERNAME = ""  # Will be set dynamically on startup

# State timeout (5 minutes)
STATE_TIMEOUT = 300

# Only 25 approved gift cards (All US-based)
GIFT_CARDS = [
    {"name": "Amazon", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"},
    {"name": "American Express", "logo": "https://upload.wikimedia.org/wikipedia/commons/f/fa/American_Express_logo_%282018%29.svg"},
    {"name": "AMEX SERVE", "logo": "https://www.serve.com/assets/images/serve-logo.svg"},
    {"name": "Apple / iTunes", "logo": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"},
    {"name": "Best Buy", "logo": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Best_Buy_Logo.svg"},
    {"name": "eBay", "logo": "https://upload.wikimedia.org/wikipedia/commons/1/1b/EBay_logo.svg"},
    {"name": "Footlocker", "logo": "https://logos-world.net/wp-content/uploads/2020/11/Foot-Locker-Logo.png"},
    {"name": "GameStop", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gamestop_logo.svg"},
    {"name": "Google Play", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/78/Google_Play_Store_badge_EN.svg"},
    {"name": "JC Penney", "logo": "https://logos-world.net/wp-content/uploads/2020/11/JCPenney-Logo.png"},
    {"name": "Nike", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg"},
    {"name": "Nordstrom", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/36/Nordstrom_logo.svg"},
    {"name": "OffGamers", "logo": "https://www.offgamers.com/images/logo.png"},
    {"name": "PlayStation", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/00/PlayStation_logo.svg"},
    {"name": "Razer Gold", "logo": "https://assets.razerzone.com/eeimages/support/products/1555/razer-gold-icon.png"},
    {"name": "Roblox", "logo": "https://upload.wikimedia.org/wikipedia/commons/8/83/Roblox_Logo.svg"},
    {"name": "Saks", "logo": "https://logos-world.net/wp-content/uploads/2021/02/Saks-Fifth-Avenue-Logo.png"},
    {"name": "Sephora", "logo": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Sephora_logo.svg"},
    {"name": "Steam", "logo": "https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg"},
    {"name": "Target", "logo": "https://upload.wikimedia.org/wikipedia/commons/9/9a/Target_logo.svg"},
    {"name": "Target Visa", "logo": "https://logos-world.net/wp-content/uploads/2020/11/Target-Logo.png"},
    {"name": "Vanilla Visa", "logo": "https://www.vanillagift.com/images/vanilla-logo.svg"},
    {"name": "Walmart", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg"},
    {"name": "Walmart Visa", "logo": "https://corporate.walmart.com/content/dam/corporate/images/logos/walmart-logos.svg"},
    {"name": "Xbox", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d7/Xbox_logo_%282019%29.svg"},
]

# Cards per page
CARDS_PER_PAGE = 8

# Crypto payment wallets
PAYMENT_WALLETS = {
    "BTC": {
        "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",  # Replace with your BTC address
        "network": "Bitcoin",
        "name": "Bitcoin (BTC)"
    },
    "USDT_TRC20": {
        "address": "TQn4Y7kQgJLmNiMKCVaJ8gN8N5qH9KwXYg",  # Replace with your USDT TRC20 address
        "network": "TRC20 (Tron)",
        "name": "USDT (TRC20)"
    },
    "USDT_ERC20": {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Replace with your USDT ERC20 address
        "network": "ERC20 (Ethereum)",
        "name": "USDT (ERC20)"
    },
    "ETH": {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Replace with your ETH address
        "network": "Ethereum",
        "name": "Ethereum (ETH)"
    }
}