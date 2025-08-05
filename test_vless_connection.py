#!/usr/bin/env python3
"""
Simple test script to check VLESS gRPC connection
"""

import json

def test_vless_connection():
    """Test VLESS gRPC connection"""
    print("🔍 Testing VLESS gRPC connection...")
    
    # Test connection to localhost:62789
    api_address = "127.0.0.1:62789"
    
    try:
        # Import grpc here to avoid issues
        import grpc
        from app.proxyman.command import command_pb2, command_pb2_grpc
        from common.protocol import user_pb2
        from common.serial import typed_message_pb2
        
        # Test basic gRPC connection
        print(f"📡 Connecting to {api_address}...")
        channel = grpc.insecure_channel(api_address)
        
        # Test creating a stub
        stub = command_pb2_grpc.HandlerServiceStub(channel)
        print("✅ HandlerServiceStub created successfully")
        
        # Test a simple request (just to see if the service responds)
        print("🧪 Testing basic gRPC request...")
        
        # Create account first
        account = typed_message_pb2.TypedMessage(
            type="xray.proxy.vless.Account",
            value=json.dumps({
                "id": "test-uuid",
                "flow": "xtls-rprx-vision"
            }).encode()
        )
        
        # Create user with properly serialized account
        user = user_pb2.User(
            level=0,
            email="test-user",
            account=account.SerializeToString()
        )
        
        # Create the request
        request = command_pb2.AlterInboundRequest(
            tag="vless-in",  # The tag of your VLESS inbound
            operation=typed_message_pb2.TypedMessage(
                type="xray.app.proxyman.command.AddUserOperation",
                value=user.SerializeToString()
            )
        )
        
        print("✅ Request object created successfully")
        print("📋 Request details:")
        print(f"   - Tag: {request.tag}")
        print(f"   - Operation type: {request.operation.type}")
        
        # Try to make the actual call
        print("🚀 Making gRPC call...")
        response = stub.AlterInbound(request)
        print("✅ gRPC call successful!")
        print(f"📤 Response: {response}")
        
        return True
        
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()}")
        print(f"📝 Details: {e.details()}")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

if __name__ == "__main__":
    success = test_vless_connection()
    if success:
        print("\n🎉 VLESS connection test PASSED!")
    else:
        print("\n💥 VLESS connection test FAILED!") 