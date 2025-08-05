#!/usr/bin/env python3
"""
Test script to check Xray gRPC API connectivity via localhost (SSH tunnel)
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
    host = "127.0.0.1"  # Localhost via SSH tunnel
    port = 62789
    
    print(f"Testing connection to {host}:{port} (via SSH tunnel)")
    print("=" * 60)
    
    # Test basic connectivity
    if test_connection(host, port):
        # Test gRPC
        test_grpc_connection(host, port)
    else:
        print("\n🔧 SSH tunnel not working. Make sure you ran:")
        print("ssh -L 62789:127.0.0.1:62789 root@77.110.110.205 -N")
        print("\nOr deploy the bot directly on the VPS for production use.") 