#!/usr/bin/env python3
"""
Test script to check Xray gRPC API connectivity
"""

import grpc
import socket

def test_connection(host, port):
    """Test if the port is open and accessible."""
    try:
        # Test basic TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is open on {host}")
            return True
        else:
            print(f"❌ Port {port} is closed on {host}")
            return False
    except Exception as e:
        print(f"❌ Error testing connection to {host}:{port}: {e}")
        return False

def test_grpc_connection(host, port):
    """Test gRPC connection."""
    try:
        channel = grpc.insecure_channel(f"{host}:{port}")
        # Try to connect with a timeout
        import time
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                # Try to get the channel state
                state = channel._channel.check_connectivity_state(True)
                if state == grpc.ChannelConnectivity.READY:
                    print(f"✅ gRPC connection successful to {host}:{port}")
                    return True
                time.sleep(0.1)
            except:
                time.sleep(0.1)
        
        print(f"❌ gRPC connection failed to {host}:{port}")
        return False
    except Exception as e:
        print(f"❌ gRPC Error: {e}")
        return False

if __name__ == "__main__":
    host = "77.110.110.205"
    port = 62789
    
    print(f"Testing connection to {host}:{port}")
    print("=" * 50)
    
    # Test basic connectivity
    if test_connection(host, port):
        # Test gRPC
        test_grpc_connection(host, port)
    else:
        print("\n🔧 To fix this, you need to:")
        print("1. SSH into your server")
        print("2. Add gRPC API configuration to your Xray config.json")
        print("3. Restart Xray service") 