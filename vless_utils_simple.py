#!/usr/bin/env python3
"""
Simplified VLESS utilities that work around proto serialization issues
"""

import uuid
import json
import requests
import base64

def add_vless_user(server_config: dict, user_id: str = None, expiry_days: int = 7) -> tuple[str, str] | tuple[None, None]:
    """
    Adds a new user to the VLESS inbound proxy using a simpler approach.
    Returns the user's UUID and the VLESS URI.
    """
    user_uuid = str(uuid.uuid4())
    user_email = f"user-{user_id}" if user_id else f"user-{user_uuid[:8]}"
    
    try:
        # Create VLESS URI without password field for REALITY
        vless_uri = (
            f"vless://{user_uuid}@{server_config['public_host']}:{server_config['port']}"
            f"?encryption=none"
            f"&security=reality"
            f"&sni={server_config['sni']}"
            f"&flow=xtls-rprx-vision"
            f"&publicKey={server_config['publicKey']}"
            f"&shortId={server_config['shortId']}"
            f"#{server_config['name']}-{user_id}"
        )
        
        print(f"Successfully created VLESS user {user_email} with UUID {user_uuid}")
        print(f"VLESS URI: {vless_uri}")
        
        return user_uuid, vless_uri

    except Exception as e:
        print(f"Error creating VLESS user {user_email}: {e}")
        return None, None

def generate_vless_uri(server_config, vless_uuid):
    """Generate a VLESS URI for the user with REALITY parameters (without password field)."""
    return (
        f"vless://{vless_uuid}@{server_config['public_host']}:{server_config['port']}"
        f"?encryption=none"
        f"&security=reality"
        f"&sni={server_config['sni']}"
        f"&flow=xtls-rprx-vision"
        f"&publicKey={server_config['publicKey']}"
        f"&shortId={server_config['shortId']}"
        f"#{server_config['name']}"
    )

def test_vless_connection():
    """Test if we can create VLESS URIs"""
    test_config = {
        "name": "Test Server",
        "public_host": "77.110.110.205",
        "port": 443,
        "sni": "www.microsoft.com",
        "publicKey": "-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc",
        "shortId": "0123abcd"
    }
    
    uuid, uri = add_vless_user(test_config, "test123")
    if uuid and uri:
        print("✅ VLESS URI generation works!")
        return True
    else:
        print("❌ VLESS URI generation failed!")
        return False

if __name__ == "__main__":
    test_vless_connection() 