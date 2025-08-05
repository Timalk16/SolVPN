# Enhanced VLESS VPN Bot

This enhanced version of the VLESS bot integrates user management functionality from `manage_users.py` with the existing Telegram bot structure. It supports two management modes for handling VLESS users.

## Features

- 🤖 **Telegram Bot Interface** - Easy-to-use commands for users
- 🔄 **Dual Management Modes** - Support for both gRPC API and direct config.json modification
- 📊 **User Management** - Add, remove, and track user subscriptions
- 🗄️ **Database Integration** - SQLite database for subscription tracking
- 🔒 **REALITY Protocol** - Enhanced security with REALITY protocol
- ⚡ **Automatic Configuration** - Seamless Xray configuration updates

## Management Modes

### 1. gRPC API Mode (Default)

- Uses Xray's gRPC API to add/remove users
- Requires Xray to be configured with API enabled
- More dynamic and real-time user management
- Set `MANAGEMENT_MODE=grpc` (default)

### 2. Config File Mode

- Directly modifies `/usr/local/etc/xray/config.json`
- Restarts Xray service after changes
- Works with the `init_server.py` setup
- Set `MANAGEMENT_MODE=config_file`

## Installation & Setup

### 1. Prerequisites

```bash
# Install required packages
pip install python-telegram-bot python-dotenv grpcio grpcio-tools

# Ensure Xray is installed and configured
# Run init_server.py first if using config_file mode
```

### 2. Environment Variables

Create a `.env` file:

```env
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Management Mode (optional, defaults to 'grpc')
MANAGEMENT_MODE=grpc  # or 'config_file'

# VLESS Configuration (for gRPC mode)
VLESS_HOST=127.0.0.1
VLESS_API_PORT=62789
VLESS_PUBLIC_HOST=77.110.110.205
VLESS_PORT=443
VLESS_SNI=www.microsoft.com
VLESS_PUBLIC_KEY=your_public_key_here
VLESS_SHORT_ID=your_short_id_here
```

### 3. Server Setup

#### For gRPC Mode:

1. Configure Xray with API enabled
2. Set up your VLESS server configuration
3. Update `vless_config.py` with your server details

#### For Config File Mode:

1. Run `init_server.py` to initialize the server
2. Ensure Xray service is running
3. The bot will automatically manage the config.json file

## Usage

### Bot Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show help information
- `/vless_subscribe` - Get VLESS VPN access
- `/my_subscription` - Check your current subscription status
- `/admin_remove <user_id>` - Admin command to remove a user (admin only)

### User Flow

1. **User subscribes**: Sends `/vless_subscribe`
2. **Bot creates user**: Adds user to Xray configuration
3. **Bot generates URI**: Creates VLESS URI with REALITY parameters
4. **Bot stores data**: Saves subscription to database
5. **User gets access**: Receives VLESS URI for connection

### Admin Commands

```bash
# Remove a user's subscription
/admin_remove 123456789
```

## Testing

Run the test script to verify functionality:

```bash
python3 test_enhanced_vless_bot.py
```

## File Structure

```
├── vless_only_bot_enhanced.py    # Enhanced bot with dual management
├── vless_config.py               # Server configuration
├── vless_database.py             # Database functions
├── vless_utils.py                # gRPC utilities
├── test_enhanced_vless_bot.py   # Test script
└── ENHANCED_VLESS_BOT_README.md # This file
```

## Configuration Files

### For gRPC Mode

The bot uses `vless_config.py` to define server parameters:

```python
VLESS_SERVERS = {
    "server1": {
        "name": "VLESS Server 1",
        "host": "127.0.0.1",
        "api_port": 62789,
        "public_host": "77.110.110.205",
        "port": 443,
        "sni": "www.microsoft.com",
        "publicKey": "your_public_key",
        "shortId": "your_short_id",
    }
}
```

### For Config File Mode

The bot reads from:

- `/usr/local/etc/xray/config.json` - Xray configuration
- `/usr/local/etc/xray/server_info.json` - Server information

## Database Schema

The bot uses SQLite to track subscriptions:

```sql
CREATE TABLE vless_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    vless_uuid TEXT,
    vless_uri TEXT,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    status TEXT DEFAULT 'active'
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### Common Issues

1. **gRPC Connection Failed**

   - Check if Xray API is enabled
   - Verify API port and host settings
   - Ensure Xray service is running

2. **Config File Not Found**

   - Run `init_server.py` first
   - Check file permissions
   - Verify Xray installation path

3. **Database Errors**
   - Check SQLite permissions
   - Ensure database directory is writable
   - Verify database schema

### Logs

The bot provides detailed logging:

- User actions and subscriptions
- Configuration changes
- Error messages and debugging info

## Migration from Original Bot

If you're migrating from the original `vless_only_bot.py`:

1. **Backup your data**: Export existing subscriptions if any
2. **Update configuration**: Set appropriate environment variables
3. **Choose management mode**: Decide between gRPC or config file mode
4. **Test thoroughly**: Use the test script before deployment
5. **Deploy gradually**: Start with a small user group

## Security Considerations

- ✅ Admin commands are restricted to ADMIN_USER_ID
- ✅ User subscriptions are tracked and managed
- ✅ REALITY protocol provides enhanced security
- ✅ Database stores subscription history
- ⚠️ Ensure proper file permissions for config files
- ⚠️ Keep bot token and admin ID secure

## Performance

- **gRPC Mode**: Faster user operations, real-time updates
- **Config File Mode**: More reliable, works with any Xray setup
- **Database**: Lightweight SQLite for subscription tracking
- **Memory**: Minimal footprint, suitable for VPS deployment

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs for error messages
3. Test with the provided test script
4. Verify your server configuration

---

**Note**: This enhanced bot maintains compatibility with your existing `init_server.py` and `manage_users.py` scripts while providing a user-friendly Telegram interface.
