#!/usr/bin/env python3
"""
Migration script to update the database schema from old format to new format.
This script will:
1. Backup the existing database
2. Update the subscriptions table schema
3. Migrate existing data to the new format
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "vpn_subscriptions.db"
BACKUP_PATH = f"vpn_subscriptions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the existing database."""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
    else:
        print("⚠️ No existing database found, creating new one")

def migrate_database():
    """Migrate the database to the new schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if we need to migrate
        cursor.execute("PRAGMA table_info(subscriptions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'duration_plan_id' in columns and 'country_package_id' in columns:
            print("✅ Database already has the new schema")
            return
        
        print("🔄 Migrating database schema...")
        
        # Create new subscriptions table with updated schema
        cursor.execute('''
            CREATE TABLE subscriptions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                duration_plan_id TEXT,
                country_package_id TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'pending_payment',
                payment_id TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create subscription_countries table
        cursor.execute('''
            CREATE TABLE subscription_countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER,
                country_code TEXT,
                outline_key_id TEXT,
                outline_access_url TEXT,
                FOREIGN KEY(subscription_id) REFERENCES subscriptions_new(id) ON DELETE CASCADE
            )
        ''')
        
        # Migrate existing data
        cursor.execute('''
            INSERT INTO subscriptions_new 
            (id, user_id, duration_plan_id, start_date, end_date, status, payment_id)
            SELECT id, user_id, plan_id, start_date, end_date, status, payment_id
            FROM subscriptions
        ''')
        
        # Migrate VPN keys to subscription_countries table
        cursor.execute('''
            INSERT INTO subscription_countries 
            (subscription_id, country_code, outline_key_id, outline_access_url)
            SELECT id, 'germany', outline_key_id, outline_access_url
            FROM subscriptions
            WHERE outline_key_id IS NOT NULL AND outline_key_id != ''
        ''')
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE subscriptions")
        cursor.execute("ALTER TABLE subscriptions_new RENAME TO subscriptions")
        
        # Update country_package_id for existing subscriptions
        cursor.execute('''
            UPDATE subscriptions 
            SET country_package_id = '5_countries' 
            WHERE country_package_id IS NULL AND status = 'active'
        ''')
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Show migration results
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        sub_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subscription_countries")
        country_count = cursor.fetchone()[0]
        
        print(f"📊 Migration results:")
        print(f"   - Subscriptions migrated: {sub_count}")
        print(f"   - Country entries created: {country_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def verify_migration():
    """Verify that the migration was successful."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check new schema
        cursor.execute("PRAGMA table_info(subscriptions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = ['duration_plan_id', 'country_package_id']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Migration verification failed. Missing columns: {missing_columns}")
            return False
        
        # Check subscription_countries table
        cursor.execute("PRAGMA table_info(subscription_countries)")
        country_columns = [column[1] for column in cursor.fetchall()]
        
        if not country_columns:
            print("❌ Migration verification failed. subscription_countries table not found")
            return False
        
        print("✅ Migration verification passed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration function."""
    print("🔄 Starting database migration...")
    
    # Step 1: Backup
    backup_database()
    
    # Step 2: Migrate
    migrate_database()
    
    # Step 3: Verify
    if verify_migration():
        print("\n🎉 Database migration completed successfully!")
        print(f"📁 Backup saved as: {BACKUP_PATH}")
    else:
        print("\n❌ Migration verification failed!")
        print("Please check the backup and try again.")

if __name__ == "__main__":
    main() 