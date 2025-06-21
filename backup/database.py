import sqlite3
import datetime
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_id TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            outline_key_id TEXT,
            outline_access_url TEXT,
            status TEXT DEFAULT 'pending_payment', -- pending_payment, active, expired, cancelled
            payment_id TEXT, -- For tracking payments with gateways
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user_if_not_exists(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                       (user_id, username, first_name))
        conn.commit()
    conn.close()

def create_subscription_record(user_id, plan_id, duration_days):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create a pending record, activation happens after payment
    cursor.execute('''
        INSERT INTO subscriptions (user_id, plan_id, status)
        VALUES (?, ?, 'pending_payment')
    ''', (user_id, plan_id))
    subscription_db_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subscription_db_id

def activate_subscription(subscription_db_id, outline_key_id, outline_access_url, duration_days, payment_id="MANUAL_CRYPTO"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    start_date = datetime.datetime.utcnow()
    end_date = start_date + datetime.timedelta(days=duration_days)
    cursor.execute('''
        UPDATE subscriptions
        SET start_date = ?, end_date = ?, outline_key_id = ?, outline_access_url = ?, status = 'active', payment_id = ?
        WHERE id = ?
    ''', (start_date, end_date, outline_key_id, outline_access_url, payment_id, subscription_db_id))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_db_id} activated. Ends on {end_date}")

def get_active_subscriptions(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, plan_id, end_date, outline_access_url, status FROM subscriptions
        WHERE user_id = ? AND status = 'active' AND end_date > CURRENT_TIMESTAMP
        ORDER BY end_date DESC
    ''', (user_id,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_expired_soon_or_active_subscriptions():
    """Gets subscriptions that are active or will expire soon (for checking)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check subscriptions that are active and their end_date is in the past
    cursor.execute('''
        SELECT id, user_id, outline_key_id, status, end_date FROM subscriptions
        WHERE status = 'active'
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def mark_subscription_expired(subscription_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET status = 'expired' WHERE id = ?", (subscription_id,))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_id} marked as expired in DB.")


# admin 
def get_all_active_subscriptions_for_admin():
    """Gets all active or recently expired subscriptions for admin view."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Fetches active or pending ones, or recently expired ones for cleanup.
    # You might want to filter by status more specifically.
    cursor.execute('''
        SELECT s.id, s.user_id, u.username, u.first_name, s.plan_id, s.end_date, s.outline_key_id, s.status
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.status IN ('active', 'pending_payment', 'expired')
        ORDER BY s.user_id, s.end_date DESC
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_subscription_by_id(subscription_db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, outline_key_id, status, outline_access_url
        FROM subscriptions
        WHERE id = ?
    ''', (subscription_db_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def cancel_subscription_by_admin(subscription_db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET status = 'cancelled_by_admin' WHERE id = ?", (subscription_db_id,))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    print(f"Subscription {subscription_db_id} marked as 'cancelled_by_admin' in DB.")
    return updated_rows > 0
   

if __name__ == '__main__':
    init_db() # Initialize DB when script is run directly
    print("Database initialized.")