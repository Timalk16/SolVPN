import uuid
from xray_api.client import XrayClient

# --- VLESS User Management ---

def get_xray_client(api_address: str, api_port: int) -> XrayClient:
    """Initializes and returns an XrayClient."""
    try:
        client = XrayClient(api_address, api_port)
        return client
    except Exception as e:
        print(f"Error initializing Xray client: {e}")
        return None

def add_vless_user(server_config: dict, user_id: str = None, expiry_days: int = 7) -> tuple[str, str] | tuple[None, None]:
    """
    Adds a new user to the VLESS inbound proxy.
    Returns the user's UUID and the VLESS URI for a REALITY setup.
    """
    client = get_xray_client(server_config['host'], server_config['api_port'])
    if not client:
        return None, None

    # Generate a unique UUID for the new user
    user_uuid = str(uuid.uuid4())
    
    # The 'email' field in Xray is used as a unique identifier for the user.
    # We'll use the user_id from Telegram to create a unique email.
    user_email = f"user-{user_id}" if user_id else f"user-{user_uuid[:8]}"

    try:
        # Add the user to the VLESS inbound (identified by its tag)
        client.add_user(inbound_tag="vless-in", email=user_email, uuid=user_uuid)
        print(f"Successfully added VLESS user {user_email} with UUID {user_uuid}")

        # Construct the VLESS URI with REALITY parameters
        # These parameters MUST match your server's config.json
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
        # Note: 'fp' (fingerprint) can also be added for better camouflage, e.g., &fp=chrome

        return user_uuid, vless_uri

    except Exception as e:
        print(f"Error adding VLESS user {user_email}: {e}")
        return None, None

def remove_vless_user(server_config: dict, user_id: str) -> bool:
    """Removes a user from the VLESS inbound proxy."""
    client = get_xray_client(server_config['host'], server_config['api_port'])
    if not client:
        return False

    user_email = f"user-{user_id}"
    try:
        client.remove_user(inbound_tag="vless-in", email=user_email)
        print(f"Successfully removed VLESS user {user_email}")
        return True
    except Exception as e:
        # Xray's API might error if the user doesn't exist, which is fine.
        if "not found" in str(e):
             print(f"User {user_email} not found for deletion, considering it a success.")
             return True
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
        "public_host": "your.domain.com", # Your server's public domain or IP
        "port": 443,                  # The public port for VLESS
        "security": "reality",        # or "tls" or other
        "network": "tcp",             # or "ws"
        "name": "MyVLESSServer"
        # Add other params like ws_path, ws_host if you use WebSocket
    }
    
    test_user_id = "12345678"
    
    print("--- Testing VLESS User Addition ---")
    new_uuid, new_uri = add_vless_user(test_server_config, test_user_id)
    if new_uuid:
        print(f"Created URI: {new_uri}")
    
    print("\n--- Testing VLESS User Removal ---")
    success = remove_vless_user(test_server_config, test_user_id)
    print(f"Removal successful: {success}") 