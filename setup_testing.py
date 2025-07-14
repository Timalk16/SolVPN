#!/usr/bin/env python3
"""
Setup script for Telegram Bot Testing
Helps configure and run the test harness
"""

import os
import sys
import subprocess
import asyncio

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'telegram',
        'aiohttp',
        'pillow'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("Dependencies installed successfully!")
    else:
        print("All dependencies are already installed.")

def get_bot_token():
    """Get bot token from user or environment"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Bot token not found in environment variables.")
        token = input("Please enter your bot token: ").strip()
        if not token:
            print("Bot token is required!")
            sys.exit(1)
    return token

def get_user_id():
    """Get test user ID from user or environment"""
    user_id = os.getenv("TEST_USER_ID")
    if not user_id:
        print("Test user ID not found in environment variables.")
        user_id = input("Please enter your Telegram user ID: ").strip()
        if not user_id:
            print("Test user ID is required!")
            sys.exit(1)
    return int(user_id)

def create_env_file(bot_token, user_id):
    """Create .env file for easy configuration"""
    env_content = f"""# Telegram Bot Testing Configuration
TELEGRAM_BOT_TOKEN={bot_token}
TEST_USER_ID={user_id}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Created .env file with your configuration.")

def load_env_file():
    """Load environment variables from .env file"""
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        print("Loaded configuration from .env file.")

def run_basic_tests():
    """Run basic test suite"""
    print("\nRunning basic test suite...")
    try:
        subprocess.run([sys.executable, "test_bot_flows.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Basic tests failed with exit code {e.returncode}")
        return False
    return True

def run_advanced_tests():
    """Run advanced test suite"""
    print("\nRunning advanced test suite...")
    try:
        subprocess.run([sys.executable, "advanced_bot_tester.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Advanced tests failed with exit code {e.returncode}")
        return False
    return True

def main():
    """Main setup function"""
    print("=== Telegram Bot Testing Setup ===\n")
    
    # Check dependencies
    print("1. Checking dependencies...")
    check_dependencies()
    
    # Load existing configuration
    print("\n2. Loading configuration...")
    load_env_file()
    
    # Get configuration
    print("\n3. Getting configuration...")
    bot_token = get_bot_token()
    user_id = get_user_id()
    
    # Create .env file
    print("\n4. Creating configuration file...")
    create_env_file(bot_token, user_id)
    
    # Set environment variables for current session
    os.environ["TELEGRAM_BOT_TOKEN"] = bot_token
    os.environ["TEST_USER_ID"] = str(user_id)
    
    # Ask user what to run
    print("\n5. Choose what to run:")
    print("1. Run basic tests only")
    print("2. Run advanced tests only")
    print("3. Run both test suites")
    print("4. Exit without running tests")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        success = run_basic_tests()
    elif choice == "2":
        success = run_advanced_tests()
    elif choice == "3":
        success1 = run_basic_tests()
        success2 = run_advanced_tests()
        success = success1 and success2
    elif choice == "4":
        print("Setup complete! You can run tests later with:")
        print("python test_bot_flows.py")
        print("python advanced_bot_tester.py")
        return
    else:
        print("Invalid choice!")
        return
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the reports for details.")
    
    print("\nSetup complete! You can run tests anytime with:")
    print("python test_bot_flows.py")
    print("python advanced_bot_tester.py")

if __name__ == "__main__":
    main() 