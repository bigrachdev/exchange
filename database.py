import sqlite3
import uuid
from config import DB_NAME, GIFT_CARDS
from datetime import datetime, timedelta

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
            balance REAL DEFAULT 0.0,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Gift cards table (simplified - no country)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gift_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            logo_url TEXT
        )
    ''')
    
    # Rates table (simplified)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_card_name TEXT UNIQUE,
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
            type TEXT,
            gift_card_name TEXT,
            denomination REAL,
            calculated_amount REAL,
            status TEXT DEFAULT 'pending',
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
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
            method TEXT,
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
    
    # Insert approved gift cards
    for card in GIFT_CARDS:
        cursor.execute('INSERT OR IGNORE INTO gift_cards (name, logo_url) VALUES (?, ?)', 
                      (card['name'], card['logo']))
        cursor.execute('INSERT OR IGNORE INTO rates (gift_card_name) VALUES (?)', 
                      (card['name'],))
    
    conn.commit()
    conn.close()

# User functions
def add_user(user_id, username, referred_by=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    referral_code = uuid.uuid4().hex[:8].upper()
    cursor.execute('''INSERT OR IGNORE INTO users (user_id, username, referral_code, referred_by) 
                     VALUES (?, ?, ?, ?)''', (user_id, username, referral_code, referred_by))
    conn.commit()
    conn.close()

def update_last_activity(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
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

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT username, balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    # Get transaction count
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = "completed"', (user_id,))
    tx_count = cursor.fetchone()[0]
    
    # Get referral count
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    ref_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'username': user[0] if user else 'Unknown',
        'balance': user[1] if user else 0.0,
        'transactions': tx_count,
        'referrals': ref_count
    }

# Gift card functions
def get_all_gift_cards():
    """Get all gift cards sorted alphabetically"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name, logo_url FROM gift_cards ORDER BY name')
    results = cursor.fetchall()
    conn.close()
    return results

def get_gift_card_logo(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT logo_url FROM gift_cards WHERE name = ?', (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Rate functions
def get_random_rate(gift_card_name, is_buy=False):
    import random
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if is_buy:
        cursor.execute('SELECT buy_min_rate, buy_max_rate FROM rates WHERE gift_card_name = ?', (gift_card_name,))
    else:
        cursor.execute('SELECT min_rate, max_rate FROM rates WHERE gift_card_name = ?', (gift_card_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        min_r, max_r = result
        return random.uniform(min_r, max_r)
    return random.uniform(5, 25) if not is_buy else random.uniform(10, 30)

# Transaction functions
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
    if status == 'completed':
        cursor.execute('''UPDATE transactions SET status = ?, reason = ?, completed_at = CURRENT_TIMESTAMP 
                         WHERE tx_id = ?''', (status, reason, tx_id))
    else:
        cursor.execute('UPDATE transactions SET status = ?, reason = ? WHERE tx_id = ?', (status, reason, tx_id))
    conn.commit()
    conn.close()

def get_transaction(tx_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE tx_id = ?', (tx_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_transactions(user_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT tx_id, type, gift_card_name, denomination, calculated_amount, status, created_at 
                     FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''', (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def get_trending_cards(limit=5):
    """Get trending gift cards based on completed transactions in last 7 days"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        SELECT gift_card_name, COUNT(*) as count 
        FROM transactions 
        WHERE status = 'completed' AND created_at > ?
        GROUP BY gift_card_name 
        ORDER BY count DESC 
        LIMIT ?
    ''', (week_ago, limit))
    results = cursor.fetchall()
    conn.close()
    return results

# Referral functions
def get_referral_code(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
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

def get_referred_by(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_referrals_count(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result

def reward_exists(referrer_id, referred_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM rewards WHERE referrer_id = ? AND referred_id = ? LIMIT 1', 
                  (referrer_id, referred_id))
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

def get_reward(reward_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rewards WHERE id = ?', (reward_id,))
    result = cursor.fetchone()
    conn.close()
    return result

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

# Withdrawal functions
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

def get_user_withdrawals(user_id, limit=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT wd_id, method, amount, status, created_at 
                     FROM withdrawals WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''', (user_id, limit))
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

# Inventory functions
def add_inventory(gift_card_name, code, denomination):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (gift_card_name, code, denomination) VALUES (?, ?, ?)', 
                  (gift_card_name, code, denomination))
    conn.commit()
    conn.close()

def get_available_code(gift_card_name, denomination):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT code FROM inventory 
                     WHERE gift_card_name = ? AND denomination = ? AND available = TRUE LIMIT 1''', 
                  (gift_card_name, denomination))
    result = cursor.fetchone()
    if result:
        code = result[0]
        cursor.execute('UPDATE inventory SET available = FALSE WHERE code = ?', (code,))
        conn.commit()
    conn.close()
    return result[0] if result else None

# Admin functions
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, balance FROM users ORDER BY user_id')
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_transactions(status=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM transactions WHERE status = ? ORDER BY created_at DESC', (status,))
    else:
        cursor.execute('SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50')
    results = cursor.fetchall()
    conn.close()
    return results

def update_rate(gift_card_name, min_rate, max_rate, buy_min=None, buy_max=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if buy_min and buy_max:
        cursor.execute('''
            UPDATE rates SET min_rate = ?, max_rate = ?, buy_min_rate = ?, buy_max_rate = ?
            WHERE gift_card_name = ?
        ''', (min_rate, max_rate, buy_min, buy_max, gift_card_name))
    else:
        cursor.execute('UPDATE rates SET min_rate = ?, max_rate = ? WHERE gift_card_name = ?', 
                      (min_rate, max_rate, gift_card_name))
    conn.commit()
    conn.close()