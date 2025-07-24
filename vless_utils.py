import os
import uuid
import requests

VLESS_API_URL = os.getenv("VLESS_API_URL")  # e.g., http://77.110.110.205:55237/hiig4yW7LdzDG6RGzj/api/
VLESS_API_USERNAME = os.getenv("VLESS_API_USERNAME")
VLESS_API_PASSWORD = os.getenv("VLESS_API_PASSWORD")

class VlessAPI:
    def __init__(self, api_url=None, username=None, password=None):
        self.api_url = api_url or VLESS_API_URL
        self.username = username or VLESS_API_USERNAME
        self.password = password or VLESS_API_PASSWORD
        self.session = requests.Session()
        self.token = None
        self.login()

    def login(self):
        """Authenticate with 3x-ui API and store the session token."""
        url = self.api_url.rstrip("/") + "/login"
        data = {"username": self.username, "password": self.password}
        resp = self.session.post(url, json=data)
        if resp.status_code == 200 and resp.json().get("success"):
            self.token = resp.json()["data"]["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise Exception(f"3x-ui API login failed: {resp.text}")

    def add_vless_user(self, inbound_id, remark=None, expiry_days=7):
        """Add a VLESS user to the specified inbound (server). Returns (uuid, uri)."""
        # Generate UUID for user
        vless_uuid = str(uuid.uuid4())
        if not remark:
            remark = f"bot_{vless_uuid[:8]}"
        # Prepare payload
        url = self.api_url.rstrip("/") + "/xui/inbound/addClient"
        payload = {
            "id": inbound_id,  # The inbound ID for your VLESS server
            "settings": {
                "clients": [
                    {
                        "id": vless_uuid,
                        "flow": "",  # Adjust if you use XTLS-Flow
                        "email": remark
                    }
                ]
            },
            "expiryTime": expiry_days * 24 * 3600  # in seconds
        }
        resp = self.session.post(url, json=payload)
        if resp.status_code == 200 and resp.json().get("success"):
            return vless_uuid
        else:
            raise Exception(f"Failed to add VLESS user: {resp.text}")

    def remove_vless_user(self, inbound_id, vless_uuid):
        """Remove a VLESS user from the specified inbound."""
        url = self.api_url.rstrip("/") + "/xui/inbound/delClient"
        payload = {
            "id": inbound_id,
            "email": vless_uuid  # 3x-ui may use email or id; adjust as needed
        }
        resp = self.session.post(url, json=payload)
        if resp.status_code == 200 and resp.json().get("success"):
            return True
        else:
            raise Exception(f"Failed to remove VLESS user: {resp.text}")

    def get_inbounds(self):
        """Get all inbounds (servers) from 3x-ui."""
        url = self.api_url.rstrip("/") + "/xui/inbound/list"
        resp = self.session.get(url)
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json()["data"]
        else:
            raise Exception(f"Failed to get inbounds: {resp.text}")

def generate_vless_uri(server_config, vless_uuid):
    """Generate a VLESS URI for the user."""
    host = server_config["host"]
    port = server_config["port"]
    return f"vless://{vless_uuid}@{host}:{port}?encryption=none#VPN-Bot-User"

# Example usage for bot flow:
def add_vless_user(server_config, user_id=None, expiry_days=7):
    """Add a VLESS user via 3x-ui API and return (uuid, uri)."""
    api = VlessAPI()
    # Find the correct inbound ID for this server
    inbounds = api.get_inbounds()
    inbound_id = None
    for inbound in inbounds:
        if inbound["listen"] == server_config["host"] or inbound["remark"] == server_config["name"]:
            inbound_id = inbound["id"]
            break
    if not inbound_id:
        raise Exception("No matching inbound found for this server.")
    vless_uuid = api.add_vless_user(inbound_id, remark=str(user_id), expiry_days=expiry_days)
    uri = generate_vless_uri(server_config, vless_uuid)
    return vless_uuid, uri

def remove_vless_user(server_config, vless_uuid):
    api = VlessAPI()
    # Find the correct inbound ID for this server
    inbounds = api.get_inbounds()
    inbound_id = None
    for inbound in inbounds:
        if inbound["listen"] == server_config["host"] or inbound["remark"] == server_config["name"]:
            inbound_id = inbound["id"]
            break
    if not inbound_id:
        raise Exception("No matching inbound found for this server.")
    return api.remove_vless_user(inbound_id, vless_uuid) 