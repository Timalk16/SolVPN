#!/usr/bin/env python3
"""
Migration script to upgrade from single-country to multi-country VPN bot
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the existing database."""
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found. Nothing to migrate.")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False

def check_old_schema(db_path):
    """Check if the database has the old single-country schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the old schema exists (subscriptions table with outline_key_id column)
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    has_old_schema = 'outline_key_id' in columns
    has_new_schema = 'subscription_countries' in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    conn.close()
    
    if has_old_schema and not has_new_schema:
        print("✅ Old single-country schema detected")
        return True
    elif has_new_schema:
        print("✅ New multi-country schema already exists")
        return False
    else:
        print("❌ Unknown database schema")
        return None

def migrate_data(db_path):
    """Migrate data from old schema to new schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create the new subscription_countries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER,
                country_code TEXT,
                outline_key_id TEXT,
                outline_access_url TEXT,
                FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
            )
        ''')
        
        # Get all subscriptions with outline keys
        cursor.execute('''
            SELECT id, outline_key_id, outline_access_url 
            FROM subscriptions 
            WHERE outline_key_id IS NOT NULL AND outline_access_url IS NOT NULL
        ''')
        
        old_subscriptions = cursor.fetchall()
        migrated_count = 0
        
        for sub_id, outline_key_id, outline_access_url in old_subscriptions:
            # Add to subscription_countries table with 'germany' as default country
            cursor.execute('''
                INSERT INTO subscription_countries (subscription_id, country_code, outline_key_id, outline_access_url)
                VALUES (?, ?, ?, ?)
            ''', (sub_id, 'germany', outline_key_id, outline_access_url))
            migrated_count += 1
        
        # Remove the old columns from subscriptions table
        cursor.execute('ALTER TABLE subscriptions DROP COLUMN outline_key_id')
        cursor.execute('ALTER TABLE subscriptions DROP COLUMN outline_access_url')
        
        conn.commit()
        print(f"✅ Migrated {migrated_count} subscriptions to multi-country schema")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main migration function."""
    db_path = "vpn_subscriptions.db"
    
    print("🔄 VPN Bot Migration: Single-Country to Multi-Country")
    print("=" * 50)
    
    # Step 1: Backup database
    if not backup_database(db_path):
        return
    
    # Step 2: Check schema
    schema_type = check_old_schema(db_path)
    if schema_type is None:
        print("❌ Cannot determine database schema. Migration aborted.")
        return
    elif schema_type is False:
        print("✅ Database is already using the new multi-country schema.")
        return
    
    # Step 3: Confirm migration
    print("\n⚠️  This will migrate your existing single-country subscriptions to the new multi-country format.")
    print("   - Existing subscriptions will be assigned to 'Germany' as the default country")
    print("   - All data will be preserved")
    print("   - A backup has been created")
    
    response = input("\nDo you want to proceed with the migration? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled.")
        return
    
    # Step 4: Perform migration
    print("\n🔄 Migrating database...")
    if migrate_data(db_path):
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your .env file with the new multi-country configuration")
        print("2. Restart your VPN bot")
        print("3. Test the new functionality")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        print("You can restore from the backup if needed.")

if __name__ == "__main__":
    main() 