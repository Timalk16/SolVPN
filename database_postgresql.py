import psycopg2
import psycopg2.extras
import datetime
from config import POSTGRES_URL, USE_POSTGRESQL

def get_connection():
    """Get a PostgreSQL connection."""
    if not USE_POSTGRESQL:
        raise ValueError("PostgreSQL is not enabled in configuration")
    return psycopg2.connect(POSTGRES_URL)

def init_db():
    """Initialize PostgreSQL database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            duration_plan_id VARCHAR(50),
            country_package_id VARCHAR(50),
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending_payment',
            payment_id VARCHAR(255),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Subscription countries table - links subscriptions to countries and their VPN keys
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_countries (
            id SERIAL PRIMARY KEY,
            subscription_id INTEGER,
            country_code VARCHAR(50),
            outline_key_id VARCHAR(255),
            outline_access_url TEXT,
            FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON subscriptions(end_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_countries_subscription_id ON subscription_countries(subscription_id)')
    
    conn.commit()
    conn.close()
    print("PostgreSQL database initialized successfully.")

def add_user_if_not_exists(user_id, username, first_name):
    """Add a user if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s)",
                       (user_id, username, first_name))
        conn.commit()
    conn.close()

def create_subscription_record(user_id, duration_plan_id, duration_days):
    """Create a pending subscription record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscriptions (user_id, duration_plan_id, status)
        VALUES (%s, %s, 'pending_payment')
        RETURNING id
    ''', (user_id, duration_plan_id))
    subscription_db_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return subscription_db_id

def update_subscription_country_package(subscription_id, country_package_id):
    """Update subscription with the selected country package."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscriptions
        SET country_package_id = %s
        WHERE id = %s
    ''', (country_package_id, subscription_id))
    conn.commit()
    conn.close()

def add_subscription_country(subscription_id, country_code, outline_key_id, outline_access_url):
    """Add a country to a subscription with its VPN key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscription_countries (subscription_id, country_code, outline_key_id, outline_access_url)
        VALUES (%s, %s, %s, %s)
    ''', (subscription_id, country_code, outline_key_id, outline_access_url))
    conn.commit()
    conn.close()

def activate_subscription(subscription_db_id, duration_days, payment_id="MANUAL_CRYPTO"):
    """Activate a subscription with start and end dates."""
    conn = get_connection()
    cursor = conn.cursor()
    start_date = datetime.datetime.utcnow()
    end_date = start_date + datetime.timedelta(days=duration_days)
    cursor.execute('''
        UPDATE subscriptions
        SET start_date = %s, end_date = %s, status = 'active', payment_id = %s
        WHERE id = %s
    ''', (start_date, end_date, payment_id, subscription_db_id))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_db_id} activated. Ends on {end_date}")

def get_active_subscriptions(user_id):
    """Get all active subscriptions for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.duration_plan_id, s.country_package_id, s.end_date, s.status,
               STRING_AGG(sc.country_code, ',') as countries,
               STRING_AGG(sc.outline_access_url, ',') as access_urls
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.user_id = %s AND s.status = 'active' AND s.end_date > CURRENT_TIMESTAMP
        GROUP BY s.id, s.duration_plan_id, s.country_package_id, s.end_date, s.status
        ORDER BY s.end_date DESC
    ''', (user_id,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_subscription_countries(subscription_id):
    """Get all countries and their VPN keys for a specific subscription."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT country_code, outline_key_id, outline_access_url
        FROM subscription_countries
        WHERE subscription_id = %s
    ''', (subscription_id,))
    countries = cursor.fetchall()
    conn.close()
    return countries

def get_expired_soon_or_active_subscriptions():
    """Gets subscriptions that are active or will expire soon (for checking)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.user_id, s.status, s.end_date,
               STRING_AGG(sc.outline_key_id, ',') as key_ids,
               STRING_AGG(sc.country_code, ',') as countries
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.status = 'active'
        GROUP BY s.id, s.user_id, s.status, s.end_date
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def mark_subscription_expired(subscription_id):
    """Mark a subscription as expired."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET status = 'expired' WHERE id = %s", (subscription_id,))
    conn.commit()
    conn.close()
    print(f"Subscription {subscription_id} marked as expired in DB.")

def get_all_active_subscriptions_for_admin():
    """Gets all active or recently expired subscriptions for admin view."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.user_id, u.username, u.first_name, s.duration_plan_id, s.country_package_id, s.end_date, s.status,
               STRING_AGG(sc.country_code, ',') as countries
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.status IN ('active', 'pending_payment', 'expired')
        GROUP BY s.id, s.user_id, u.username, u.first_name, s.duration_plan_id, s.country_package_id, s.end_date, s.status
        ORDER BY s.user_id, s.end_date DESC
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_subscription_by_id(subscription_id):
    """Get subscription details by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, duration_plan_id, country_package_id, start_date, end_date, status, payment_id
        FROM subscriptions
        WHERE id = %s
    ''', (subscription_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def get_subscription_for_admin(subscription_id):
    """Get subscription details by ID in the format expected by admin functions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.user_id, s.status,
               STRING_AGG(sc.outline_key_id, ',') as key_ids,
               STRING_AGG(sc.country_code, ',') as countries
        FROM subscriptions s
        LEFT JOIN subscription_countries sc ON s.id = sc.subscription_id
        WHERE s.id = %s
        GROUP BY s.id, s.user_id, s.status
    ''', (subscription_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def cancel_subscription_by_admin(subscription_db_id):
    """Cancel a subscription by admin."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE subscriptions SET status = 'cancelled_by_admin' WHERE id = %s", (subscription_db_id,))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    print(f"Subscription {subscription_db_id} marked as 'cancelled_by_admin' in DB.")
    return updated_rows > 0

if __name__ == '__main__':
    init_db()  # Initialize DB when script is run directly
    print("PostgreSQL database initialized.") 