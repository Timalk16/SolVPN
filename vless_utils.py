import uuid
import requests
import json

# --- VLESS User Management ---

def get_xray_client(api_address: str, api_port: int):
    """Initializes and returns Xray API base URL."""
    return f"http://{api_address}:{api_port}"

def add_vless_user(server_config: dict, user_id: str = None, expiry_days: int = 7) -> tuple[str, str] | tuple[None, None]:
    """
    Adds a new user to the VLESS inbound proxy via Xray HTTP API.
    Returns the user's UUID and the VLESS URI for a REALITY setup.
    """
    api_url = get_xray_client(server_config['host'], server_config['api_port'])
    
    # Generate a unique UUID for the new user
    user_uuid = str(uuid.uuid4())
    
    # The 'email' field in Xray is used as a unique identifier for the user.
    user_email = f"user-{user_id}" if user_id else f"user-{user_uuid[:8]}"

    try:
        # Add user via Xray HTTP API
        add_user_url = f"{api_url}/inbound/addUser"
        payload = {
            "tag": "vless-in",  # Your inbound tag
            "email": user_email,
            "uuid": user_uuid
        }
        
        response = requests.post(add_user_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Successfully added VLESS user {user_email} with UUID {user_uuid}")
            
            # Construct the VLESS URI with REALITY parameters
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
            
            return user_uuid, vless_uri
        else:
            print(f"Failed to add user: {response.text}")
            return None, None

    except Exception as e:
        print(f"Error adding VLESS user {user_email}: {e}")
        return None, None

def remove_vless_user(server_config: dict, user_id: str) -> bool:
    """Removes a user from the VLESS inbound proxy via Xray HTTP API."""
    api_url = get_xray_client(server_config['host'], server_config['api_port'])
    user_email = f"user-{user_id}"
    
    try:
        # Remove user via Xray HTTP API
        remove_user_url = f"{api_url}/inbound/removeUser"
        payload = {
            "tag": "vless-in",  # Your inbound tag
            "email": user_email
        }
        
        response = requests.post(remove_user_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Successfully removed VLESS user {user_email}")
            return True
        else:
            print(f"Failed to remove user: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error removing VLESS user {user_email}: {e}")
        return False

def generate_vless_uri(server_config, vless_uuid):
    """Generate a VLESS URI for the user with REALITY parameters."""
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

if __name__ == '__main__':
    # --- Test Functions ---
    # Replace with your actual Xray server details for testing
    test_server_config = {
        "host": "127.0.0.1",          # The IP where the Xray API is listening
        "api_port": 62789,            # The port for the Xray API
        "public_host": "77.110.110.205", # Your server's public domain or IP
        "port": 443,                  # The public port for VLESS
        "sni": "www.github.com",      # SNI
        "publicKey": "-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc", # Public key
        "shortId": "0123abcd",        # Short ID
        "name": "TestVLESSServer"
    }
    
    test_user_id = "12345678"
    
    print("--- Testing VLESS User Addition ---")
    new_uuid, new_uri = add_vless_user(test_server_config, test_user_id)
    if new_uuid:
        print(f"Created URI: {new_uri}")
    
    print("\n--- Testing VLESS User Removal ---")
    success = remove_vless_user(test_server_config, test_user_id)
    print(f"Removal successful: {success}") 