#!/usr/bin/env python3
"""
Hybrid VLESS utilities - generates URIs and manages users via config file
"""

import uuid
import json
import os
from typing import Tuple, Optional

def add_vless_user(server_config: dict, user_id: str = None, expiry_days: int = 7) -> Tuple[Optional[str], Optional[str]]:
    """
    Adds a new user to the VLESS config file and generates a working URI.
    Returns the user's UUID and the VLESS URI.
    """
    user_uuid = str(uuid.uuid4())
    user_email = f"user-{user_id}" if user_id else f"user-{user_uuid[:8]}"
    
    try:
        # Read the current Xray config
        config_path = "/usr/local/etc/xray/config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find the VLESS inbound
        vless_inbound = None
        for inbound in config.get('inbounds', []):
            if inbound.get('tag') == 'vless-in':
                vless_inbound = inbound
                break
        
        if not vless_inbound:
            print("Error: VLESS inbound not found in config")
            return None, None
        
        # Add the new user to the clients list
        new_client = {
            "id": user_uuid,
            "email": user_email,
            "flow": "xtls-rprx-vision"
        }
        
        vless_inbound['settings']['clients'].append(new_client)
        
        # Write the updated config back
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Successfully added VLESS user {user_email} with UUID {user_uuid}")
        
        # Generate the VLESS URI
        vless_uri = generate_vless_uri(server_config, user_uuid, user_id)
        
        return user_uuid, vless_uri
        
    except Exception as e:
        print(f"Error adding VLESS user {user_email}: {e}")
        return None, None

def remove_vless_user(server_config: dict, user_id: str) -> bool:
    """Removes a user from the VLESS config file."""
    user_email = f"user-{user_id}"
    
    try:
        # Read the current Xray config
        config_path = "/usr/local/etc/xray/config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find the VLESS inbound
        vless_inbound = None
        for inbound in config.get('inbounds', []):
            if inbound.get('tag') == 'vless-in':
                vless_inbound = inbound
                break
        
        if not vless_inbound:
            print("Error: VLESS inbound not found in config")
            return False
        
        # Remove the user from the clients list
        clients = vless_inbound['settings']['clients']
        vless_inbound['settings']['clients'] = [
            client for client in clients if client.get('email') != user_email
        ]
        
        # Write the updated config back
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Successfully removed VLESS user {user_email}")
        return True
        
    except Exception as e:
        print(f"Error removing VLESS user {user_email}: {e}")
        return False

def generate_vless_uri(server_config: dict, vless_uuid: str, user_id: str = None) -> str:
    """
    Generates a VLESS URI with REALITY protocol parameters.
    """
    name_suffix = f"-{user_id}" if user_id else ""
    
    vless_uri = (
        f"vless://{vless_uuid}@{server_config['public_host']}:{server_config['port']}"
        f"?encryption=none"
        f"&security=reality"
        f"&sni={server_config['sni']}"
        f"&flow=xtls-rprx-vision"
        f"&publicKey={server_config['publicKey']}"
        f"&shortId={server_config['shortId']}"
        f"&password={vless_uuid}"
        f"#{server_config['name']}{name_suffix}"
    )
    
    return vless_uri

def reload_xray_config() -> bool:
    """Reloads the Xray configuration by sending a SIGHUP signal."""
    try:
        import subprocess
        # Find Xray process and send SIGHUP
        result = subprocess.run(['pgrep', '-f', 'xray'], capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            subprocess.run(['kill', '-HUP', pid])
            print("Xray configuration reloaded successfully")
            return True
        else:
            print("Xray process not found")
            return False
    except Exception as e:
        print(f"Error reloading Xray config: {e}")
        return False 