#!/usr/bin/env python3
"""
Database functions for VLESS-only Telegram Bot
"""

import sqlite3
import datetime
from vless_config import DB_PATH

def init_vless_db():
    """Initialize VLESS subscriptions table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vless_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vless_uuid TEXT,
            vless_uri TEXT,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            expiry_date TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Users table (if not exists)
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
    print("VLESS database initialized successfully")

def add_vless_subscription(user_id, vless_uuid, vless_uri, expiry_date):
    """Add a new VLESS subscription."""
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
    print(f"VLESS subscription added for user {user_id}")

def get_user_subscription(user_id):
    """Get the most recent active subscription for a user."""
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

def remove_vless_subscription(user_id):
    """Remove all subscriptions for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE vless_subscriptions
        SET status = 'removed'
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    print(f"VLESS subscriptions removed for user {user_id}")

def get_vless_subscriptions(user_id):
    """Get all VLESS subscriptions for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT vless_uuid, vless_uri, start_date, end_date, status
        FROM vless_subscriptions
        WHERE user_id = ?
        ORDER BY start_date DESC
    ''', (user_id,))
    
    subscriptions = cursor.fetchall()
    conn.close()
    
    return subscriptions 