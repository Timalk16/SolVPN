#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
import os
import sys
from datetime import datetime
from config import DB_PATH, POSTGRES_URL, USE_POSTGRESQL

def get_sqlite_connection():
    """Get SQLite connection."""
    if not os.path.exists(DB_PATH):
        print(f"SQLite database file {DB_PATH} not found!")
        return None
    return sqlite3.connect(DB_PATH)

def get_postgresql_connection():
    """Get PostgreSQL connection."""
    try:
        return psycopg2.connect(POSTGRES_URL)
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return None

def migrate_users(sqlite_conn, postgres_conn):
    """Migrate users table."""
    print("Migrating users...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all users from SQLite
    sqlite_cursor.execute("SELECT user_id, username, first_name, join_date FROM users")
    users = sqlite_cursor.fetchall()
    
    if not users:
        print("No users to migrate.")
        return
    
    # Insert users into PostgreSQL
    for user in users:
        try:
            postgres_cursor.execute(
                "INSERT INTO users (user_id, username, first_name, join_date) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
                user
            )
        except Exception as e:
            print(f"Error inserting user {user[0]}: {e}")
    
    postgres_conn.commit()
    print(f"Migrated {len(users)} users.")

def migrate_subscriptions(sqlite_conn, postgres_conn):
    """Migrate subscriptions table."""
    print("Migrating subscriptions...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all subscriptions from SQLite
    sqlite_cursor.execute("""
        SELECT id, user_id, duration_plan_id, country_package_id, 
               start_date, end_date, status, payment_id 
        FROM subscriptions
    """)
    subscriptions = sqlite_cursor.fetchall()
    
    if not subscriptions:
        print("No subscriptions to migrate.")
        return
    
    # Insert subscriptions into PostgreSQL
    for sub in subscriptions:
        try:
            postgres_cursor.execute("""
                INSERT INTO subscriptions (id, user_id, duration_plan_id, country_package_id, 
                                         start_date, end_date, status, payment_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING
            """, sub)
        except Exception as e:
            print(f"Error inserting subscription {sub[0]}: {e}")
    
    postgres_conn.commit()
    print(f"Migrated {len(subscriptions)} subscriptions.")

def migrate_subscription_countries(sqlite_conn, postgres_conn):
    """Migrate subscription_countries table."""
    print("Migrating subscription countries...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all subscription countries from SQLite
    sqlite_cursor.execute("""
        SELECT id, subscription_id, country_code, outline_key_id, outline_access_url 
        FROM subscription_countries
    """)
    subscription_countries = sqlite_cursor.fetchall()
    
    if not subscription_countries:
        print("No subscription countries to migrate.")
        return
    
    # Insert subscription countries into PostgreSQL
    for sc in subscription_countries:
        try:
            postgres_cursor.execute("""
                INSERT INTO subscription_countries (id, subscription_id, country_code, 
                                                   outline_key_id, outline_access_url) 
                VALUES (%s, %s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING
            """, sc)
        except Exception as e:
            print(f"Error inserting subscription country {sc[0]}: {e}")
    
    postgres_conn.commit()
    print(f"Migrated {len(subscription_countries)} subscription countries.")

def verify_migration(sqlite_conn, postgres_conn):
    """Verify that migration was successful."""
    print("\nVerifying migration...")
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Check users count
    sqlite_cursor.execute("SELECT COUNT(*) FROM users")
    sqlite_users_count = sqlite_cursor.fetchone()[0]
    
    postgres_cursor.execute("SELECT COUNT(*) FROM users")
    postgres_users_count = postgres_cursor.fetchone()[0]
    
    print(f"Users: SQLite={sqlite_users_count}, PostgreSQL={postgres_users_count}")
    
    # Check subscriptions count
    sqlite_cursor.execute("SELECT COUNT(*) FROM subscriptions")
    sqlite_subs_count = sqlite_cursor.fetchone()[0]
    
    postgres_cursor.execute("SELECT COUNT(*) FROM subscriptions")
    postgres_subs_count = postgres_cursor.fetchone()[0]
    
    print(f"Subscriptions: SQLite={sqlite_subs_count}, PostgreSQL={postgres_subs_count}")
    
    # Check subscription countries count
    sqlite_cursor.execute("SELECT COUNT(*) FROM subscription_countries")
    sqlite_sc_count = sqlite_cursor.fetchone()[0]
    
    postgres_cursor.execute("SELECT COUNT(*) FROM subscription_countries")
    postgres_sc_count = postgres_cursor.fetchone()[0]
    
    print(f"Subscription Countries: SQLite={sqlite_sc_count}, PostgreSQL={postgres_sc_count}")
    
    # Check if counts match
    if (sqlite_users_count == postgres_users_count and 
        sqlite_subs_count == postgres_subs_count and 
        sqlite_sc_count == postgres_sc_count):
        print("✅ Migration verification successful!")
        return True
    else:
        print("❌ Migration verification failed!")
        return False

def backup_sqlite():
    """Create a backup of the SQLite database."""
    backup_filename = f"sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, backup_filename)
        print(f"SQLite database backed up to {backup_filename}")
        return backup_filename
    return None

def main():
    """Main migration function."""
    print("=== SQLite to PostgreSQL Migration Tool ===")
    
    # Check if PostgreSQL is enabled
    if not USE_POSTGRESQL:
        print("PostgreSQL is not enabled in configuration. Please set USE_POSTGRESQL=true")
        return
    
    # Get connections
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        print("Failed to connect to SQLite database.")
        return
    
    postgres_conn = get_postgresql_connection()
    if not postgres_conn:
        print("Failed to connect to PostgreSQL database.")
        sqlite_conn.close()
        return
    
    try:
        # Create backup
        backup_file = backup_sqlite()
        
        # Initialize PostgreSQL database
        print("Initializing PostgreSQL database...")
        from database_postgresql import init_db
        init_db()
        
        # Perform migration
        migrate_users(sqlite_conn, postgres_conn)
        migrate_subscriptions(sqlite_conn, postgres_conn)
        migrate_subscription_countries(sqlite_conn, postgres_conn)
        
        # Verify migration
        success = verify_migration(sqlite_conn, postgres_conn)
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print(f"SQLite backup saved as: {backup_file}")
            print("\nTo complete the migration:")
            print("1. Set USE_POSTGRESQL=true in your environment")
            print("2. Test your application with PostgreSQL")
            print("3. Once confirmed working, you can remove the SQLite backup")
        else:
            print("\n❌ Migration failed! Please check the errors above.")
            
    except Exception as e:
        print(f"Migration failed with error: {e}")
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    main() 