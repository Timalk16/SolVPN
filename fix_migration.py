#!/usr/bin/env python3
"""
Fixes a partial migration by:
- Migrating data from old subscriptions to subscriptions_new
- Dropping old subscriptions table
- Renaming subscriptions_new to subscriptions
- Ensuring country_package_id is set for active subscriptions
"""
import sqlite3
from datetime import datetime

DB_PATH = "vpn_subscriptions.db"

def fix_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check if both tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions_new'")
        if not cursor.fetchone():
            print("No subscriptions_new table found. Nothing to fix.")
            return
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
        if not cursor.fetchone():
            print("No subscriptions table found. Nothing to fix.")
            return
        print("Migrating data from old subscriptions to subscriptions_new...")
        # Copy data from old subscriptions to subscriptions_new (if not already copied)
        cursor.execute('''
            INSERT OR IGNORE INTO subscriptions_new 
            (id, user_id, duration_plan_id, start_date, end_date, status, payment_id)
            SELECT id, user_id, plan_id, start_date, end_date, status, payment_id
            FROM subscriptions
        ''')
        # Drop old subscriptions table
        print("Dropping old subscriptions table...")
        cursor.execute("DROP TABLE subscriptions")
        # Rename subscriptions_new to subscriptions
        print("Renaming subscriptions_new to subscriptions...")
        cursor.execute("ALTER TABLE subscriptions_new RENAME TO subscriptions")
        # Set country_package_id for active subscriptions if missing
        print("Setting country_package_id for active subscriptions...")
        cursor.execute('''
            UPDATE subscriptions 
            SET country_package_id = '5_countries' 
            WHERE country_package_id IS NULL AND status = 'active'
        ''')
        conn.commit()
        print("✅ Migration fix complete!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration fix: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_migration() 