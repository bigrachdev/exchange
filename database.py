import sqlite3
import uuid
from config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table with balance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            balance REAL DEFAULT 0.0
        )
    ''')
    
    # Gift cards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gift_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            name TEXT UNIQUE,
            logo_url TEXT
        )
    ''')
    
    # Rates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_card_name TEXT,
            country TEXT,
            min_rate REAL DEFAULT 5.0,
            max_rate REAL DEFAULT 25.0,
            buy_min_rate REAL DEFAULT 10.0,
            buy_max_rate REAL DEFAULT 30.0,
            FOREIGN KEY (gift_card_name) REFERENCES gift_cards(name)
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id TEXT PRIMARY KEY,
            user_id INTEGER,
            type TEXT,  -- 'sell' or 'buy'
            gift_card_name TEXT,
            denomination REAL,
            calculated_amount REAL,
            status TEXT DEFAULT 'pending',  -- pending, verified, completed, failed
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Inventory for buy side
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_card_name TEXT,
            code TEXT UNIQUE,
            denomination REAL,
            available BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (gift_card_name) REFERENCES gift_cards(name)
        )
    ''')
    
    # Rewards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            amount REAL DEFAULT 5.0,
            status TEXT DEFAULT 'pending',
            tx_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Withdrawals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            wd_id TEXT PRIMARY KEY,
            user_id INTEGER,
            method TEXT,  -- 'bank' or 'crypto'
            amount REAL,
            fee REAL,
            net_amount REAL,
            details TEXT,
            status TEXT DEFAULT 'pending',
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Insert initial gift cards if not exist
    initial_gift_cards = [
        # USA
        ("USA", "Amazon US", "https://1000logos.net/wp-content/uploads/2016/10/Amazon-Logo.png"),
        ("USA", "Google Play US", "https://logos-world.net/wp-content/uploads/2020/12/Google-Play-Logo.png"),
        ("USA", "iTunes US", "https://w7.pngwing.com/pngs/754/558/png-transparent-itunes-logo-itunes-store-logo-podcast-music-others-label-text-black-thumbnail.png"),
        ("USA", "Steam US", "https://img.itch.zone/aW1nLzE4MzUyNzU5LnBuZw==/original/8DRbfb.png"),
        ("USA", "Xbox US", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Xbox_logo_%282019%29.svg"),
        ("USA", "Walmart US", "https://brandcenter.walmart.com/content/dam/brand/home/brand-identity/wordmark/DoNotLockupTheSparkToTheRight.svg"),
        ("USA", "Sephora US", "https://assets.stickpng.com/images/5a1aca40f65d84088faf138d.png"),
        ("USA", "Target US", "https://1000logos.net/wp-content/uploads/2017/06/Target-logo-1.png"),
        ("USA", "Visa US", "https://1000logos.net/wp-content/uploads/2021/11/VISA-logo.png"),
        ("USA", "eBay US", "https://1000logos.net/wp-content/uploads/2018/10/Ebay-Logo-1.png"),
        ("USA", "Netflix US", "https://upload.wikimedia.org/wikipedia/commons/f/fd/Netflix-Logo.png"),
        ("USA", "Starbucks US", "https://logos-world.net/wp-content/uploads/2020/09/Starbucks-Logo.png"),
        ("USA", "Best Buy US", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Best_Buy_Logo.svg/2560px-Best_Buy_Logo.svg.png"),
        ("USA", "Home Depot US", "https://download.logo.wine/logo/The_Home_Depot/The_Home_Depot-Logo.wine.png"),
        ("USA", "Lyft US", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Lyft_logo.svg/2560px-Lyft_logo.svg.png"),
        ("USA", "Instacart US", "https://logos-world.net/wp-content/uploads/2022/02/Instacart-Logo.png"),
        ("USA", "Gap US", "https://logos-world.net/wp-content/uploads/2020/09/Gap-Logo.png"),
        ("USA", "Abercrombie & Fitch US", "https://assets.stickpng.com/images/61586daa258f1e000415491a.png"),
        ("USA", "Everlane US", "https://findlogovector.com/wp-content/uploads/2018/11/everlane-logo-vector.png"),
        ("USA", "J.Crew US", "https://cdn.freebiesupply.com/logos/thumbs/2x/j-crew-logo.png"),
        ("USA", "Quince US", "https://cdn.prod.website-files.com/636efe803b9c9d4237062457/66c347290af97bb28b79c730_e5XtoS7eq2y8qaqdI8r25nxXyPmmM4Wb076kZBT3kIE.png"),
        ("USA", "Chewy US", "https://1000logos.net/wp-content/uploads/2024/08/Chewy-Logo.jpg"),

        # UK
        ("UK", "Amazon UK", "https://image.similarpng.com/file/similarpng/very-thumbnail/2020/06/Amazon.co.png"),
        ("UK", "Google Play UK", "https://media.tokenstore.io/8b/90/8b908f2c-a0b5-49aa-afc1-3750b7807f39.png"),
        ("UK", "iTunes UK", "https://images.squarespace-cdn.com/content/v1/55fba586e4b0ee63468b8451/1592445942888-QZDHJ7E3NCJEY1AUBTF5/blue-uk-itunes.png"),
        ("UK", "Tesco UK", "https://homestartcentrallancs.org.uk/wp-content/uploads/2018/12/Tesco-logo-vector.png"),
        ("UK", "Prezzo UK", "https://assets.motivates.co.uk/m/lifestyle/brand/Prezzo_Logo%20Blue%20(002).png"),
        ("UK", "Steam UK", "https://spaces.filmstories.co.uk/uploads/2023/09/steam-logo-3.png"),
        ("UK", "IKEA UK", "https://www.computing.co.uk/interview/2024/media_10b931c42b8934338024c74e10783bfc22d7bf6ea.png?width=750&format=png&optimize=medium"),
        ("UK", "Netflix UK", "https://agsd.org.uk/wp-content/uploads/2019/08/netflix-logo-rgb-16470_1080x675.png"),
        ("UK", "John Lewis UK", "https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/John_Lewis_%26_Partners_logo.svg/1200px-John_Lewis_%26_Partners_logo.svg.png"),
        ("UK", "Marks & Spencer UK", "https://corporate.marksandspencer.com/sites/marksandspencer/files/03-2024/MandS_Logo_Masterbrand_Primary_Blk_RGB.jpg"),
        ("UK", "Argos UK", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Argos_logo.svg/1200px-Argos_logo.svg.png"),
        ("UK", "Selfridges UK", "https://www.creativeartcourses.org/wp-content/uploads/selfridges-logo-1024x575-1400x786.jpg"),
        ("UK", "Currys UK", "https://www.currysplc.com/media/lj3en515/1.png"),
        ("UK", "ASOS UK", "https://1000logos.net/wp-content/uploads/2021/04/Asos-logo.png"),
        ("UK", "Deliveroo UK", "https://logos-world.net/wp-content/uploads/2021/02/Deliveroo-Logo.png"),
        ("UK", "Just Eat UK", "https://1000logos.net/wp-content/uploads/2021/12/Just-Eat-logo.png"),
        ("UK", "Harrods UK", "https://1000logos.net/wp-content/uploads/2020/09/Harrods-Logo.png"),
        ("UK", "Fortnum & Mason UK", "https://i.pinimg.com/736x/51/a0/fd/51a0fd71664a5a0bf430af7f52358cec.jpg"),
        ("UK", "Harvey Nichols UK", "https://www.vilasa.co.uk/wp-content/uploads/2019/08/Harvey-Nichols-Logo.png"),
        ("UK", "Happy Holidays Choice UK", "https://www.giftcard.co.uk/sites/default/files/2025-10/Feestdagen-GC-UK-choice-gift-card-happy-holidays_GOUDFOLIE.png?v=w1000"),
        ("UK", "Home & Garden UK", "https://www.ribblevalleybathrooms.co.uk/wp-content/uploads/2021/01/HomeGardens-black-logo.png"),
        ("UK", "All in one Choice UK", "https://onechoiceapparel.co.uk/cdn/shop/files/Asset_977_6423865a-bdec-44cc-a180-098ee77bac18.png?v=1670240792"),
        ("UK", "National Garden UK", "http://www.plymouthgardencentre.co.uk/cdn/shop/files/NGGCLogo_RGBPurple.png?v=1756729405"),
        ("UK", "Hotel Gift UK", "https://www.hotelgiftcard.com/sites/default/files/2024-11/HotelGiftcard-UK_4.png"),

        # Canada
        ("Canada", "Amazon CA", "https://s3.amazonaws.com/cdn.help.the3doodler.com/20200427221750/amazonca-logo.jpg"),
        ("Canada", "Home Depot CA", "https://logos-world.net/wp-content/uploads/2021/08/Home-Depot-Logo.png"),
        ("Canada", "PlayStation CA", "https://gmedia.playstation.com/is/image/SIEPDC/ps-default-listing-thumb-05oct20?$facebook$"),
        ("Canada", "Walmart CA", "https://download.logo.wine/logo/Walmart_Canada/Walmart_Canada-Logo.wine.png"),
        ("Canada", "Best Buy CA", "https://s47748.pcdn.co/wp-content/uploads/2025/08/Best-Buy-CA-Logo.png"),
        ("Canada", "Apple CA", "https://www.apple.com/ac/structured-data/images/open_graph_logo.png?202110180743"),
        ("Canada", "Bass Pro Shops CA", "https://assets.basspro.com/image/upload/v1757359674/DigitalCreative/2025/BPS_CAB/Sitelets/Misc./Media-Center/08-29-2025/Bass-Pro-Shops-Logo-No-Signature.png?$bpssite_default$"),
        ("Canada", "Boston Pizza CA", "https://static.wikia.nocookie.net/logopedia/images/d/d8/Boston-pizza1.svg/revision/latest/scale-to-width-down/300?cb=20250406202921"),
        ("Canada", "Burger King CA", "https://static4.franchisedirect.ie/dims4/default/876326e/2147483647/strip/true/crop/350x184+0+18/resize/1200x630!/quality/95/?url=https%3A%2F%2Ffranchisedirect-40-prod-ops.s3.amazonaws.com%2F48%2Fcb%2Fd5cbb2101186078636c8cb6adbfb%2Fburger-king.png"),
        ("Canada", "Netflix CA", "https://thefulcrum.ca/wp-content/uploads/2022/09/netflix_logo.png"),
        ("Canada", "Roblox CA", "https://thedeepdive.ca/wp-content/uploads/2022/02/roblox-logo.png"),
        ("Canada", "Xbox CA", "https://assets.play.xbox.com/playxbox/static/media/CloudGaming_LetterBox.scale-200.ef909bf4.png"),
        ("Canada", "Gap CA", "https://assets.bidali.com/commerce/brands/gap.png"),
        ("Canada", "Razer Gold CA", "https://media.gold.razer.com/paymentwall/channels/logos/1/logo.png"),
        ("Canada", "Loblaw CA", "https://dis-prod.assetful.loblaw.ca/content/dam/loblaw-companies-limited/creative-assets/loblaw-ca/cropped-for-web/home/Loblaws-CMYK-web.jpg"),
        ("Canada", "Cineplex CA", "https://mma.prnewswire.com/media/2767457/Cineplex_Cineplex_Reports_August_Box_Office_Results.jpg?p=twitter"),
        ("Canada", "Shell CA", "https://civmin.utoronto.ca/wp-content/uploads/2023/01/Shell-Logo-1024x576-1.png"),
        ("Canada", "Esso CA", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Esso_textlogo.svg/1200px-Esso_textlogo.svg.png"),
        ("Canada", "Petro-Canada CA", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Petro-Canada_logo.svg/1200px-Petro-Canada_logo.svg.png"),
        ("Canada", "Tim Hortons CA", "https://original.fontsinuse.com/fontsinuse.com/use-images/168/168941/168941.png"),
        ("Canada", "Everlane CA", "https://i.ebayimg.com/00/s/OTU3WDE2MDA=/z/dVYAAOSwzV9mVfnT/$_57.PNG?set_id=880000500F"),
        ("Canada", "Lululemon CA", "https://thedeepdive.ca/wp-content/uploads/2022/06/lululemon-logo.png"),
        ("Canada", "Urban Outfitters CA", "https://1000logos.net/wp-content/uploads/2023/04/Urban-Outfitters-Logo.png"),
        ("Canada", "Simons CA", "https://www.simonscareers.ca/static/vb/355/stock-handling.webp"),
        ("Canada", "Away CA", "https://visitamadorcity.com/wp-content/uploads/2024/07/Away_to_Amador_City_web-11-600x438.png"),

        # Australia
        ("Australia", "Amazon AU", "https://m.media-amazon.com/images/I/413Ais4J2uL.jpg"),
        ("Australia", "Apple AU", "https://external-preview.redd.it/FhKEnZSaSMLgjYmWxCk8AeoX9Wxe3ooRvpOZiAc6e1I.jpg?width=640&crop=smart&auto=webp&s=cd02e9eb1b8372e756422d32008f4a7b67b39f9d"),
        ("Australia", "Google Play AU", "https://accesspay.com.au/wp-content/uploads/google-play-logo.png"),
        ("Australia", "Netflix AU", "https://www.edigitalagency.com.au/wp-content/uploads/Netflix-logo-red-black-png.png"),
        ("Australia", "Steam AU", "https://www.edigitalagency.com.au/wp-content/uploads/Steam-logo-black-PNG.png"),
        ("Australia", "Uber AU", "https://stickerart.com.au/images/temp/images-products-1807-10233-uber_logo_white-w500-c0.png"),
        ("Australia", "Visa AU", "https://www.visa.com.au/dam/VCOM/regional/ve/romania/blogs/hero-image/visa-logo-800x450.jpg"),
        ("Australia", "Ultimate Gift Cards AU", "https://www.ultimategiftcards.com.au/wp-content/uploads/2022/08/00-Ultimate-O4A-Digital-Occasion-Everyone-Logos-700x422-1.png"),
        ("Australia", "Good Food AU", "https://www.nineforbrands.com.au/wp-content/uploads/2024/11/Artboard-1.png"),
        ("Australia", "Only 1 Visa AU", "https://giftcardexpress.com.au/wp-content/uploads/2020/10/1d6384d0e988a68fee57b208a6d32cf_1602562640656.png"),
        ("Australia", "Activ Visa AU", "https://activgiftcard.com.au/wp-content/uploads/2022/09/active-visa-card@2x.png"),
        ("Australia", "Vanilla Visa AU", "https://www.mygiftcardsupply.com/wp-content/uploads/2021/08/vanilla-visa-gift-card.png"),
        ("Australia", "Australia Post AU", "https://humanrights.gov.au/sites/default/files/2021-08/ap_secondarylogo_stacked_red_rgb_800px.jpg"),
        ("Australia", "Temple & Webster AU", "https://www.templeandwebstergroup.com.au/FormBuilder/_Resource/_module/7ik7dYsBn029bNaEl1204g/images/twgroup-logo-website.png"),
        ("Australia", "Myer AU", "https://hbasalon.com.au/wp-content/uploads/myer-logo-vector.png"),
        ("Australia", "Coles AU", "https://1000logos.net/wp-content/uploads/2021/08/Coles-Logo.png"),
        ("Australia", "Target AU", "https://download.logo.wine/logo/Target_Australia/Target_Australia-Logo.wine.png"),
        ("Australia", "Catch AU", "https://www.intelligentreach.com/wp-content/uploads/2020/10/catch-logo-2020-FullColour-RGB.png"),
        ("Australia", "Prezzee AU", "https://mma.prnewswire.com/media/1972311/PrezzeeLogo.jpg"),
        ("Australia", "Adore Beauty AU", "https://cdn.prod.website-files.com/5fbb892601063d4822d16704/6478444101c5003e7d4c7049_ab1.png"),
        ("Australia", "Adrenaline AU", "https://i0.wp.com/icehockeynewsaustralia.com/wp-content/uploads/2015/07/Thumbnail-Adelaide-Adrenaline.png?resize=678%2C381&ssl=1"),
        ("Australia", "Airbnb AU", "https://www.edigitalagency.com.au/wp-content/uploads/new-Airbnb-logo-black-png.png"),
        ("Australia", "Amart Furniture AU", "https://static.wikia.nocookie.net/logopedia/images/b/bd/Amart_Furniture_2023_S.svg/revision/latest?cb=20230201175422"),
        ("Australia", "Pub Crawler AU", "http://www.urbaninsider.com.au/wp-content/uploads/2013/07/pub-crawl.jpg"),

        # Germany
        ("Germany", "Amazon DE", "https://upload.wikimedia.org/wikipedia/commons/0/07/Amazon-de-logo.jpg"),
        ("Germany", "Apple DE", "https://e7.pngegg.com/pngimages/186/863/png-clipart-apple-logo-apple-logo-computer-wallpaper.png"),
        ("Germany", "Google Play DE", "https://cdn.mos.cms.futurecdn.net/Q2oLsPvoGLpzWuDqZgzANH-1920-80.jpg"),
        ("Germany", "Netflix DE", "https://e7.pngegg.com/pngimages/648/464/png-clipart-netflix-logo-netflix-logo-icons-logos-emojis-tech-companies-thumbnail.png"),
        ("Germany", "Steam DE", "https://e7.pngegg.com/pngimages/448/550/png-clipart-steam-computer-icons-logo-steam-logo-video-game.png"),
        ("Germany", "Uber DE", "https://download.logo.wine/logo/Uber/Uber-Logo.wine.png"),
        ("Germany", "Lidl DE", "https://download.logo.wine/logo/Lidl/Lidl-Logo.wine.png"),
        ("Germany", "Sony PlayStation DE", "https://www.logo.wine/a/logo/PlayStation/PlayStation-Icon-Logo.wine.svg"),
        ("Germany", "IKEA DE", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/IKEA_Foundation_Logo.png/981px-IKEA_Foundation_Logo.png"),
        ("Germany", "Sephora DE", "https://1000logos.net/wp-content/uploads/2018/08/Sephora-Logo-500x281.png"),
        ("Germany", "Freedom of Choice DE", "https://img1.wsimg.com/isteam/ip/e800060b-b545-4730-a5d0-aae452689006/blob-d64dcf0.png"),
        ("Germany", "Saturn DE", "https://www.altmarkt-galerie-dresden.de/fileadmin/user_upload/GLOBAL/brand_stores/logos/saturn.png"),
        ("Germany", "Galleria Kaufhof DE", "https://upload.wikimedia.org/wikipedia/commons/a/ac/GALERIA_Logo_2021.png"),
        ("Germany", "Media Markt DE", "https://logos-world.net/wp-content/uploads/2022/04/Media-Markt-Logo.png"),
        ("Germany", "Vinexus DE", "https://media.visable.com/https://wlw-1-company-facts-media20191122174836234900000006.s3.eu-central-1.amazonaws.com/5bd4efe9-444e-4b43-b630-5b21ab7ecf8d.png?w=500&h=500&auto=format,compress&fit=fillmax&transparency=grid&grid-colors=ffffff,ffffff"),
        ("Germany", "Harrods DE", "https://logos-world.net/wp-content/uploads/2024/09/Harrods-Logo.jpg"),
        ("Germany", "Konfetti DE", "https://w7.pngwing.com/pngs/519/372/png-transparent-confetti-confetti-holidays-text-wedding-thumbnail.png")
    ]
    
    for country, name, logo_url in initial_gift_cards:
        cursor.execute('INSERT OR IGNORE INTO gift_cards (country, name, logo_url) VALUES (?, ?, ?)', (country, name, logo_url))
    
    # Set default rates
    cursor.execute('SELECT name, country FROM gift_cards')
    for name, country in cursor.fetchall():
        cursor.execute('INSERT OR IGNORE INTO rates (gift_card_name, country) VALUES (?, ?)', (name, country))
    
    conn.commit()
    conn.close()

# User functions
def add_user(user_id, username, referred_by=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    referral_code = uuid.uuid4().hex[:8].upper()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, referral_code, referred_by) VALUES (?, ?, ?, ?)', (user_id, username, referral_code, referred_by))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0

def update_balance(user_id, amount, add=True):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    op = '+' if add else '-'
    cursor.execute(f'UPDATE users SET balance = balance {op} ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_random_rate(gift_card_name, country, is_buy=False):
    import random
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if is_buy:
        cursor.execute('SELECT buy_min_rate, buy_max_rate FROM rates WHERE gift_card_name = ? AND country = ?', (gift_card_name, country))
    else:
        cursor.execute('SELECT min_rate, max_rate FROM rates WHERE gift_card_name = ? AND country = ?', (gift_card_name, country))
    result = cursor.fetchone()
    conn.close()
    if result:
        min_r, max_r = result
        return random.uniform(min_r, max_r)
    return random.uniform(5, 25) if not is_buy else random.uniform(10, 30)

def get_gift_cards(country):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM gift_cards WHERE country = ? ORDER BY name', (country,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def get_logo_url(gift_card_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT logo_url FROM gift_cards WHERE name = ?', (gift_card_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_transaction(tx_id, user_id, tx_type, gift_card_name, denomination, calculated_amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (tx_id, user_id, type, gift_card_name, denomination, calculated_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tx_id, user_id, tx_type, gift_card_name, denomination, calculated_amount))
    conn.commit()
    conn.close()

def update_transaction_status(tx_id, status, reason=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if reason:
        cursor.execute('UPDATE transactions SET status = ?, reason = ? WHERE tx_id = ?', (status, reason, tx_id))
    else:
        cursor.execute('UPDATE transactions SET status = ? WHERE tx_id = ?', (status, tx_id))
    conn.commit()
    conn.close()

def get_transaction(tx_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE tx_id = ?', (tx_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_transactions(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_transactions(status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM transactions WHERE status = ?', (status,))
    else:
        cursor.execute('SELECT * FROM transactions')
    results = cursor.fetchall()
    conn.close()
    return results

def add_inventory(gift_card_name, code, denomination):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (gift_card_name, code, denomination) VALUES (?, ?, ?)', (gift_card_name, code, denomination))
    conn.commit()
    conn.close()

def get_available_code(gift_card_name, denomination):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM inventory WHERE gift_card_name = ? AND denomination = ? AND available = TRUE LIMIT 1', (gift_card_name, denomination))
    result = cursor.fetchone()
    if result:
        code = result[0]
        cursor.execute('UPDATE inventory SET available = FALSE WHERE code = ?', (code,))
        conn.commit()
    conn.close()
    return result[0] if result else None

def reward_exists(referrer_id, referred_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM rewards WHERE referrer_id = ? AND referred_id = ? LIMIT 1', (referrer_id, referred_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_reward(referrer_id, referred_id, tx_id, amount=5.0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rewards (referrer_id, referred_id, tx_id, amount)
        VALUES (?, ?, ?, ?)
    ''', (referrer_id, referred_id, tx_id, amount))
    reward_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reward_id

def update_reward_status(reward_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE rewards SET status = ? WHERE id = ?', (status, reward_id))
    conn.commit()
    conn.close()

def get_pending_rewards_amount(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM rewards WHERE referrer_id = ? AND status = "pending"', (user_id,))
    result = cursor.fetchone()[0] or 0.0
    conn.close()
    return result

def get_paid_rewards_amount(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM rewards WHERE referrer_id = ? AND status = "paid"', (user_id,))
    result = cursor.fetchone()[0] or 0.0
    conn.close()
    return result

def get_referrals_count(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_referred_by(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_by_referral_code(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username FROM users WHERE referral_code = ?', (code,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_referral_code(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    results = cursor.fetchall()
    conn.close()
    return results

def get_reward(reward_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rewards WHERE id = ?', (reward_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def add_gift_card(country, name, logo_url=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO gift_cards (country, name, logo_url) VALUES (?, ?, ?)', (country, name, logo_url))
    cursor.execute('INSERT OR IGNORE INTO rates (gift_card_name, country) VALUES (?, ?)', (name, country))
    conn.commit()
    conn.close()

def update_rate(gift_card_name, country, min_rate, max_rate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO rates (gift_card_name, country, min_rate, max_rate)
        VALUES (?, ?, ?, ?)
    ''', (gift_card_name, country, min_rate, max_rate))
    conn.commit()
    conn.close()

def get_all_gift_cards():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT country, name FROM gift_cards ORDER BY country, name')
    results = cursor.fetchall()
    conn.close()
    return results

def add_withdrawal(wd_id, user_id, method, amount, fee, net_amount, details):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO withdrawals (wd_id, user_id, method, amount, fee, net_amount, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (wd_id, user_id, method, amount, fee, net_amount, details))
    conn.commit()
    conn.close()

def update_withdrawal_status(wd_id, status, reason=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if reason:
        cursor.execute('UPDATE withdrawals SET status = ?, reason = ? WHERE wd_id = ?', (status, reason, wd_id))
    else:
        cursor.execute('UPDATE withdrawals SET status = ? WHERE wd_id = ?', (status, wd_id))
    conn.commit()
    conn.close()

def get_withdrawal(wd_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM withdrawals WHERE wd_id = ?', (wd_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_withdrawals(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT wd_id, method, amount, status, created_at FROM withdrawals WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_pending_withdrawals():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM withdrawals WHERE status = "pending"')
    results = cursor.fetchall()
    conn.close()
    return results