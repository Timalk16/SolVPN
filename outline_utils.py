from outline_vpn.outline_vpn import OutlineVPN
from config import OUTLINE_SERVERS
import uuid

def get_outline_client(country_code):
    """Initializes and returns an OutlineVPN client for a specific country."""
    if country_code not in OUTLINE_SERVERS:
        raise ValueError(f"Country {country_code} not found in OUTLINE_SERVERS configuration")
    
    server_config = OUTLINE_SERVERS[country_code]
    api_url = server_config["api_url"]
    
    if not api_url or "YOUR_OUTLINE_API_URL" in api_url:
        raise ValueError(f"OUTLINE_API_URL for {country_code} is not configured properly in config.py")
    
    client_params = {"api_url": api_url}
    if server_config["cert_sha256"]:
        client_params["cert_sha256"] = server_config["cert_sha256"]
    
    try:
        client = OutlineVPN(**client_params)
        return client
    except Exception as e:
        print(f"Error initializing Outline client for {country_code}: {e}")
        return None

def create_outline_key(client, key_name_prefix="user"):
    """Creates a new key on the Outline server."""
    if not client:
        print("Outline client is not available.")
        return None, None
    try:
        # The key_name_prefix argument to this function is now effectively unused
        # for the create_key call itself, but could be logged or used for other purposes if needed.
        # The actual desired name will be set by the rename_outline_key call in main.py.

        new_key = client.create_key() # Call create_key without any arguments
        
        if new_key:
            # The new_key.name will be the default name assigned by Outline (e.g., "Key 1", "Key 2")
            print(f"Successfully created Outline key. ID: {new_key.key_id}, Default Name from Server: {new_key.name}")
            return new_key.key_id, new_key.access_url
        else:
            print("Failed to create key, new_key object is None from client.create_key().")
            return None, None
            
    except Exception as e:
        print(f"Error creating Outline key: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def delete_outline_key(client, key_id):
    """Deletes a key from the Outline server."""
    if not client:
        return False
    try:
        # Ensure key_id is string if it comes from DB as int
        return client.delete_key(str(key_id))
    except Exception as e:
        print(f"Error deleting Outline key {key_id}: {e}")
        return False

def rename_outline_key(client, key_id, new_name):
    """Renames an Outline key."""
    if not client:
        return False
    try:
        return client.rename_key(str(key_id), new_name)
    except Exception as e:
        print(f"Error renaming Outline key {key_id}: {e}")
        return False

def get_available_countries():
    """Returns a list of available country codes that have configured servers."""
    return [country for country, config in OUTLINE_SERVERS.items() if config["api_url"]]

if __name__ == '__main__':
    # Test functions (ensure your OUTLINE_API_URL is set in config.py)
    available_countries = get_available_countries()
    print(f"Available countries: {available_countries}")
    
    for country in available_countries:
        print(f"\nTesting connection to {country} server...")
        client = get_outline_client(country)
        if client:
            print(f"Successfully connected to {country} Outline server.")
            try:
                server_info = client.get_server_information()
                print(f"Server name: {server_info.get('name', 'N/A')}")
                print(f"Number of keys: {len(client.get_keys())}")
            except Exception as e:
                print(f"Error getting server info for {country}: {e}")
        else:
            print(f"Failed to connect to {country} Outline server. Check config.py and server status.")

        # Example: Create and delete a test key
        # print("Creating test key...")
        # key_id, access_url = create_outline_key(client, "test_key")
        # if key_id:
        #     print(f"Created key ID: {key_id}, URL: {access_url}")
        #     print(f"Renaming key {key_id}...")
        #     rename_outline_key(client, key_id, "my_renamed_test_key")
        #     print(f"Deleting key {key_id}...")
        #     if delete_outline_key(client, key_id):
        #         print(f"Key {key_id} deleted successfully.")
        #     else:
        #         print(f"Failed to delete key {key_id}.")
        # else:
        #     print("Failed to create test key.")