#!/bin/bash

# VPN Bot Startup Script
echo "Starting VPN Bot..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Please run this script from the bot directory."
    exit 1
fi

# Check if virtual environment exists
if [ -d "source" ]; then
    echo "Activating virtual environment..."
    source source/bin/activate
fi

# Start the bot
echo "Starting bot with Python..."
python start_bot.py 