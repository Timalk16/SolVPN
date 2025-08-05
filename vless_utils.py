import uuid
import grpc
import json

# --- IMPORTANT: Import the generated files ---
# These imports will work if you ran the protoc command from your project's root
from app.proxyman.command import command_pb2, command_pb2_grpc
from common.protocol import user_pb2
from common.serial import typed_message_pb2

def add_vless_user(server_config: dict, user_id: str = None, expiry_days: int = 7) -> tuple[str, str] | tuple[None, None]:
    """
    Adds a new user to the VLESS inbound proxy using the generated gRPC client.
    Returns the user's UUID and the VLESS URI.
    """
    api_address = f"{server_config['host']}:{server_config['api_port']}"
    user_uuid = str(uuid.uuid4())
    user_email = f"user-{user_id}" if user_id else f"user-{user_uuid[:8]}"
    
    try:
        # Establish a connection channel to the Xray gRPC API
        channel = grpc.insecure_channel(api_address)
        stub = command_pb2_grpc.HandlerServiceStub(channel)

        # Create the user account data
        account_data = {
            "id": user_uuid,
            "flow": "xtls-rprx-vision"
        }
        
        # Create the request to add a user
        request = command_pb2.AlterInboundRequest(
            tag="vless-in",  # The tag of your VLESS inbound
            operation=typed_message_pb2.TypedMessage(
                type="xray.app.proxyman.command.AddUserOperation",
                value=user_pb2.User(
                    level=0,
                    email=user_email,
                    account=typed_message_pb2.TypedMessage(
                        type="xray.proxy.vless.Account",
                        value=json.dumps(account_data).encode()
                    )
                ).SerializeToString()
            )
        )
        
        # Make the gRPC call
        stub.AlterInbound(request)
        print(f"Successfully added VLESS user {user_email} with UUID {user_uuid}")

        # Construct the VLESS URI with REALITY parameters (without password field)
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

    except grpc.RpcError as e:
        print(f"gRPC Error adding VLESS user {user_email}: {e.details()}")
        return None, None
    except Exception as e:
        print(f"General Error adding VLESS user {user_email}: {e}")
        return None, None


def remove_vless_user(server_config: dict, user_id: str) -> bool:
    """Removes a user from the VLESS inbound proxy."""
    api_address = f"{server_config['host']}:{server_config['api_port']}"
    user_email = f"user-{user_id}"

    try:
        channel = grpc.insecure_channel(api_address)
        stub = command_pb2_grpc.HandlerServiceStub(channel)

        # Create the request to remove a user
        request = command_pb2.AlterInboundRequest(
            tag="vless-in",
            operation=typed_message_pb2.TypedMessage(
                type="xray.app.proxyman.command.RemoveUserOperation",
                value=user_pb2.User(email=user_email).SerializeToString()
            )
        )
        
        stub.AlterInbound(request)
        print(f"Successfully removed VLESS user {user_email}")
        return True
        
    except grpc.RpcError as e:
        # It's okay if the user is already gone.
        if "not found" in e.details():
            print(f"User {user_email} not found for deletion, considering it a success.")
            return True
        print(f"gRPC Error removing VLESS user {user_email}: {e.details()}")
        return False
    except Exception as e:
        print(f"General Error removing VLESS user {user_email}: {e}")
        return False


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
    """Test if we can add VLESS users via gRPC"""
    test_config = {
        "name": "Test Server",
        "host": "127.0.0.1",
        "api_port": 62789,
        "public_host": "77.110.110.205",
        "port": 443,
        "sni": "www.microsoft.com",
        "publicKey": "-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc",
        "shortId": "0123abcd"
    }
    
    uuid, uri = add_vless_user(test_config, "test123")
    if uuid and uri:
        print("✅ VLESS gRPC user addition works!")
        return True
    else:
        print("❌ VLESS gRPC user addition failed!")
        return False


if __name__ == "__main__":
    test_vless_connection() 