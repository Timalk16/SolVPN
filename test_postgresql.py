#!/usr/bin/env python3
"""
Test script to verify PostgreSQL setup and functionality
"""

import os
import sys
from config import USE_POSTGRESQL, POSTGRES_URL

def test_postgresql_connection():
    """Test PostgreSQL connection."""
    print("=== PostgreSQL Connection Test ===")
    
    if not USE_POSTGRESQL:
        print("❌ PostgreSQL is not enabled in configuration")
        print("Set USE_POSTGRESQL=true to enable PostgreSQL")
        return False
    
    try:
        import psycopg2
        print("✅ psycopg2 imported successfully")
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        print("✅ Connected to PostgreSQL successfully")
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL version: {version.split(',')[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    print("\n=== Database Operations Test ===")
    
    try:
        from database import init_db, add_user_if_not_exists, create_subscription_record
        
        # Initialize database
        print("Initializing database...")
        init_db()
        print("✅ Database initialized successfully")
        
        # Test user creation
        print("Testing user creation...")
        add_user_if_not_exists(12345, "test_user", "Test User")
        print("✅ User creation test passed")
        
        # Test subscription creation
        print("Testing subscription creation...")
        sub_id = create_subscription_record(12345, "1_month", 30)
        print(f"✅ Subscription creation test passed (ID: {sub_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def test_migration_script():
    """Test migration script availability."""
    print("\n=== Migration Script Test ===")
    
    if os.path.exists("migrate_to_postgresql.py"):
        print("✅ Migration script found")
        return True
    else:
        print("❌ Migration script not found")
        return False

def main():
    """Run all tests."""
    print("PostgreSQL Setup Verification")
    print("=" * 40)
    
    tests = [
        test_postgresql_connection,
        test_database_operations,
        test_migration_script
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! PostgreSQL is ready to use.")
        print("\nNext steps:")
        print("1. Set USE_POSTGRESQL=true in your environment")
        print("2. Deploy to Render with PostgreSQL database")
        print("3. Run migration script if you have existing SQLite data")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 