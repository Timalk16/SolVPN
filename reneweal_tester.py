import psycopg2
from datetime import datetime, timedelta

DB_URL = "postgresql://vpn_bot_db_user:o7luPmawamu3dEfnE2KVSKzyUUuP0ZpV@dpg-d1psnr49c44c738vo7eg-a.frankfurt-postgres.render.com/vpn_bot_db"
USER_ID = 336181581  # <-- Replace with your test user id
DURATION_DAYS = 30   # <-- Replace with your plan's duration

def get_subscription_end_date(user_id):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT end_date FROM subscriptions
        WHERE user_id = %s AND status = 'active'
        ORDER BY end_date DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # If end_date is datetime, return as is; if string, parse
        if isinstance(row[0], datetime):
            return row[0]
        else:
            return datetime.fromisoformat(row[0])
    return None

def test_subscription_renewal(user_id, duration_days):
    # 1. Get current end date
    old_end_date = get_subscription_end_date(user_id)
    print(f"Old end date: {old_end_date}")

    input("Now, renew the subscription for this user via the bot, then press Enter to continue...")

    # 2. Get new end date
    new_end_date = get_subscription_end_date(user_id)
    print(f"New end date: {new_end_date}")

    # 3. Check if new_end_date == old_end_date + duration_days
    if old_end_date and new_end_date:
        expected = old_end_date + timedelta(days=duration_days)
        print(f"Expected new end date: {expected}")
        # Allow a few minutes of difference due to processing time
        if abs((new_end_date - expected).total_seconds()) < 300:
            print("✅ Subscription renewal adds time correctly!")
        else:
            print("❌ Renewal did not add time as expected!")
    else:
        print("❌ Could not fetch subscription dates.")

if __name__ == "__main__":
    test_subscription_renewal(USER_ID, DURATION_DAYS)