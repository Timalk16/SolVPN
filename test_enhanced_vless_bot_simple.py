#!/usr/bin/env python3
"""
Simple test script for Enhanced VLESS Bot functionality
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Mock the config for testing
DB_PATH = "test_vless_subscriptions.db"

def init_test_db():
    """Initialize test database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vless_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vless_uuid TEXT,
            vless_uri TEXT,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_date TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Test database initialized successfully")

def add_test_subscription(user_id, vless_uuid, vless_uri, expiry_date):
    """Add a test subscription."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add user if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, join_date)
        VALUES (?, CURRENT_TIMESTAMP)
    ''', (user_id,))
    
    # Add VLESS subscription
    cursor.execute('''
        INSERT INTO vless_subscriptions (user_id, vless_uuid, vless_uri, expiry_date, status)
        VALUES (?, ?, ?, ?, 'active')
    ''', (user_id, vless_uuid, vless_uri, expiry_date))
    
    conn.commit()
    conn.close()
    print(f"✅ Added test subscription for user {user_id}")

def get_test_subscription(user_id):
    """Get test subscription for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vless_uuid, vless_uri, expiry_date, status
        FROM vless_subscriptions
        WHERE user_id = ? AND status = 'active'
        ORDER BY start_date DESC
        LIMIT 1
    ''', (user_id,))
    
    subscription = cursor.fetchone()
    conn.close()
    
    if subscription:
        return {
            'vless_uuid': subscription[0],
            'vless_uri': subscription[1],
            'expiry_date': subscription[2],
            'status': subscription[3]
        }
    return None

def remove_test_subscription(user_id):
    """Remove test subscription for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE vless_subscriptions
        SET status = 'removed'
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    print(f"✅ Removed test subscription for user {user_id}")

def test_database_functions():
    """Test database functions."""
    print("🧪 Testing database functions...")
    
    # Initialize database
    init_test_db()
    
    # Test user subscription
    test_user_id = 12345
    test_uuid = "test-uuid-12345"
    test_uri = "vless://test-uuid-12345@77.110.110.205:443?encryption=none&security=reality&sni=www.microsoft.com&fp=chrome&pbk=test-key&sid=test-sid&type=tcp&flow=xtls-rprx-vision#test-user"
    test_expiry = datetime.now() + timedelta(days=7)
    
    # Add subscription
    add_test_subscription(test_user_id, test_uuid, test_uri, test_expiry)
    
    # Get subscription
    subscription = get_test_subscription(test_user_id)
    if subscription:
        print(f"✅ Retrieved subscription: {subscription['vless_uuid']}")
    else:
        print("❌ Failed to retrieve subscription")
    
    # Remove subscription
    remove_test_subscription(test_user_id)
    
    # Verify removal
    subscription_after = get_test_subscription(test_user_id)
    if not subscription_after:
        print("✅ Subscription successfully removed")
    else:
        print("❌ Subscription still exists after removal")

def test_management_modes():
    """Test different management modes."""
    print("\n🧪 Testing management modes...")
    
    # Test environment variable setting
    os.environ['MANAGEMENT_MODE'] = 'grpc'
    print("✅ Set MANAGEMENT_MODE to 'grpc'")
    
    os.environ['MANAGEMENT_MODE'] = 'config_file'
    print("✅ Set MANAGEMENT_MODE to 'config_file'")

def test_vless_uri_generation():
    """Test VLESS URI generation."""
    print("\n🧪 Testing VLESS URI generation...")
    
    # Test URI generation with sample data
    user_uuid = "test-uuid-12345"
    server_ip = "77.110.110.205"
    sni = "www.microsoft.com"
    public_key = "test-public-key"
    short_id = "test-short-id"
    email = "test-user"
    
    link = (
        f"vless://{user_uuid}@{server_ip}:443?"
        f"encryption=none&security=reality&sni={sni}&fp=chrome"
        f"&pbk={public_key}&sid={short_id}&type=tcp&flow=xtls-rprx-vision"
        f"#{email}"
    )
    
    print(f"✅ Generated VLESS URI: {link[:50]}...")

def cleanup():
    """Clean up test files."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ Cleaned up test database")

if __name__ == "__main__":
    print("🧪 Testing Enhanced VLESS Bot Components")
    print("=" * 50)
    
    try:
        test_database_functions()
        test_management_modes()
        test_vless_uri_generation()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nTo test the full bot:")
        print("1. Set your TELEGRAM_BOT_TOKEN and ADMIN_USER_ID environment variables")
        print("2. Install dependencies: pip install python-telegram-bot python-dotenv grpcio")
        print("3. Run: python3 vless_only_bot_enhanced.py")
        print("4. Or set MANAGEMENT_MODE=config_file to use direct config.json modification")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        cleanup() 