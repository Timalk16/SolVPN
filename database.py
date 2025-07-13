import sqlite3
import datetime
from config import DB_PATH, USE_POSTGRESQL

# Import PostgreSQL functions if PostgreSQL is enabled
if USE_POSTGRESQL:
    try:
        from database_postgresql import (
            init_db as init_postgresql_db,
            add_user_if_not_exists as add_user_if_not_exists_postgresql,
            create_subscription_record as create_subscription_record_postgresql,
            update_subscription_country_package as update_subscription_country_package_postgresql,
            add_subscription_country as add_subscription_country_postgresql,
            activate_subscription as activate_subscription_postgresql,
            get_active_subscriptions as get_active_subscriptions_postgresql,
            get_subscription_countries as get_subscription_countries_postgresql,
            get_expired_soon_or_active_subscriptions as get_expired_soon_or_active_subscriptions_postgresql,
            mark_subscription_expired as mark_subscription_expired_postgresql,
            get_all_active_subscriptions_for_admin as get_all_active_subscriptions_for_admin_postgresql,
            get_subscription_by_id as get_subscription_by_id_postgresql,
            get_subscription_for_admin as get_subscription_for_admin_postgresql,
            cancel_subscription_by_admin as cancel_subscription_by_admin_postgresql
        )
    except ImportError:
        print("Warning: PostgreSQL module not found, falling back to SQLite")
        USE_POSTGRESQL = False

def init_db():
    """Initialize database based on configuration."""
    if USE_POSTGRESQL:
        return init_postgresql_db()
    else:
        return init_sqlite_db()

def init_sqlite_db():
    """Initialize SQLite database."""
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
            duration_plan_id TEXT,
            country_package_id TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            status TEXT DEFAULT 'pending_payment', -- pending_payment, active, expired, cancelled
            payment_id TEXT, -- For tracking payments with gateways
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Subscription countries table - links subscriptions to countries and their VPN keys
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER,
            country_code TEXT, -- e.g., 'germany', 'france'
            outline_key_id TEXT,
            outline_access_url TEXT,
            FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user_if_not_exists(user_id, username, first_name):
    """Add a user if they don't already exist."""
    if USE_POSTGRESQL:
        return add_user_if_not_exists_postgresql(user_id, username, first_name)
    else:
        return add_user_if_not_exists_sqlite(user_id, username, first_name)

def add_user_if_not_exists_sqlite(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                       (user_id, username, first_name))
        conn.commit()
    conn.close()

def create_subscription_record(user_id, duration_plan_id, duration_days):
    """Create a pending subscription record."""
    if USE_POSTGRESQL:
        return create_subscription_record_postgresql(user_id, duration_plan_id, duration_days)
    else:
        return create_subscription_record_sqlite(user_id, duration_plan_id, duration_days)

def create_subscription_record_sqlite(user_id, duration_plan_id, duration_days):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create a pending record, activation happens after payment
    cursor.execute('''
        INSERT INTO subscriptions (user_id, duration_plan_id, status)
        VALUES (?, ?, 'pending_payment')
    ''', (user_id, duration_plan_id))
    subscription_db_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subscription_db_id

def update_subscription_country_package(subscription_id, country_package_id):
    """Update subscription with the selected country package."""
    if USE_POSTGRESQL:
        return update_subscription_country_package_postgresql(subscription_id, country_package_id)
    else:
        return update_subscription_country_package_sqlite(subscription_id, country_package_id)

def update_subscription_country_package_sqlite(subscription_id, country_package_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscriptions
        SET country_package_id = ?
        WHERE id = ?
    ''', (country_package_id, subscription_id))
    conn.commit()
    conn.close()

def add_subscription_country(subscription_id, country_code, outline_key_id, outline_access_url):
    """Add a country to a subscription with its VPN key."""
    if USE_POSTGRESQL:
        return add_subscription_country_postgresql(subscription_id, country_code, outline_key_id, outline_access_url)
    else:
        return add_subscription_country_sqlite(subscription_id, country_code, outline_key_id, outline_access_url)

def add_subscription_country_sqlite(subscription_id, country_code, outline_key_id, outline_access_url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscription_countries (subscription_id, country_code, outline_key_id, outline_access_url)
        VALUES (?, ?, ?, ?)
    ''', (subscription_id, country_code, outline_key_id, outline_access_url))
    conn.commit()
    conn.close()

def activate_subscription(subscription_db_id, duration_days, payment_id="MANUAL_CRYPTO"):
    """Activate a subscription with start and end dates."""
    if USE_POSTGRESQL:
        return activate_subscription_postgresql(subscription_db_id, duration_days, payment_id)
    else:
        return activate_subscription_sqlite(subscription_db_id, duration_days, payment_id)

def activate_subscription_sqlite(subscription_db_id, duration_days, payment_id="MANUAL_CRYPTO"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    start_date = datetime.datetime.utcnow()
    end_date = start_date + datetime.timedelta(days=duration_days)
    cursor.execute('''
        UPDATE subscriptions
        SET start_date = ?, end_date = ?, status = 'active', payment_id = ?
        WHERE id = ?
    ''', (start_date, end_date, payment_id, subscription_db_id))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_db_id} activated. Ends on {end_date}")

def get_active_subscriptions(user_id):
    """Get all active subscriptions for a user."""
    if USE_POSTGRESQL:
        return get_active_subscriptions_postgresql(user_id)
    else:
        return get_active_subscriptions_sqlite(user_id)

def get_active_subscriptions_sqlite(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.duration_plan_id, s.country_package_id, s.end_date, s.status,
               GROUP_CONCAT(sc.country_code) as countries,
               GROUP_CONCAT(sc.outline_access_url) as access_urls
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.user_id = ? AND s.status = 'active' AND s.end_date > CURRENT_TIMESTAMP
        GROUP BY s.id
        ORDER BY s.end_date DESC
    ''', (user_id,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_subscription_countries(subscription_id):
    """Get all countries and their VPN keys for a specific subscription."""
    if USE_POSTGRESQL:
        return get_subscription_countries_postgresql(subscription_id)
    else:
        return get_subscription_countries_sqlite(subscription_id)

def get_subscription_countries_sqlite(subscription_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT country_code, outline_key_id, outline_access_url
        FROM subscription_countries
        WHERE subscription_id = ?
    ''', (subscription_id,))
    countries = cursor.fetchall()
    conn.close()
    return countries

def get_expired_soon_or_active_subscriptions():
    """Gets subscriptions that are active or will expire soon (for checking)."""
    if USE_POSTGRESQL:
        return get_expired_soon_or_active_subscriptions_postgresql()
    else:
        return get_expired_soon_or_active_subscriptions_sqlite()

def get_expired_soon_or_active_subscriptions_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check subscriptions that are active and their end_date is in the past
    cursor.execute('''
        SELECT s.id, s.user_id, s.status, s.end_date,
               GROUP_CONCAT(sc.outline_key_id) as key_ids,
               GROUP_CONCAT(sc.country_code) as countries
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.status = 'active'
        GROUP BY s.id
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def mark_subscription_expired(subscription_id):
    """Mark a subscription as expired."""
    if USE_POSTGRESQL:
        return mark_subscription_expired_postgresql(subscription_id)
    else:
        return mark_subscription_expired_sqlite(subscription_id)

def mark_subscription_expired_sqlite(subscription_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET status = 'expired' WHERE id = ?", (subscription_id,))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_id} marked as expired in DB.")

def get_all_active_subscriptions_for_admin():
    """Gets all active or recently expired subscriptions for admin view."""
    if USE_POSTGRESQL:
        return get_all_active_subscriptions_for_admin_postgresql()
    else:
        return get_all_active_subscriptions_for_admin_sqlite()

def get_all_active_subscriptions_for_admin_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.user_id, u.username, u.first_name, s.duration_plan_id, s.country_package_id, s.end_date, s.status,
               GROUP_CONCAT(sc.country_code) as countries
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.status IN ('active', 'pending_payment', 'expired')
        GROUP BY s.id
        ORDER BY s.user_id, s.end_date DESC
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_subscription_by_id(subscription_id):
    """Get subscription details by ID."""
    if USE_POSTGRESQL:
        return get_subscription_by_id_postgresql(subscription_id)
    else:
        return get_subscription_by_id_sqlite(subscription_id)

def get_subscription_by_id_sqlite(subscription_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, duration_plan_id, country_package_id, start_date, end_date, status, payment_id
        FROM subscriptions
        WHERE id = ?
    ''', (subscription_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def get_subscription_for_admin(subscription_id):
    """Get subscription details by ID in the format expected by admin functions."""
    if USE_POSTGRESQL:
        return get_subscription_for_admin_postgresql(subscription_id)
    else:
        return get_subscription_for_admin_sqlite(subscription_id)

def get_subscription_for_admin_sqlite(subscription_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.user_id, s.status,
               GROUP_CONCAT(sc.outline_key_id) as key_ids,
               GROUP_CONCAT(sc.country_code) as countries
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.id = ?
        GROUP BY s.id
    ''', (subscription_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def cancel_subscription_by_admin(subscription_db_id):
    """Cancel a subscription by admin."""
    if USE_POSTGRESQL:
        return cancel_subscription_by_admin_postgresql(subscription_db_id)
    else:
        return cancel_subscription_by_admin_sqlite(subscription_db_id)

def cancel_subscription_by_admin_sqlite(subscription_db_id):
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