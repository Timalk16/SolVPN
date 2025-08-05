# Enhanced VLESS Bot Deployment Guide

## 🚀 Quick Deployment

All files have been uploaded to your VPS server `77.110.110.205`. Here's how to deploy:

### 1. SSH into your server

```bash
ssh root@77.110.110.205
```

### 2. Run the setup script

```bash
cd /root
chmod +x setup_enhanced_vless_bot.sh
./setup_enhanced_vless_bot.sh
```

### 3. Configure the bot

```bash
# Copy and edit the environment file
cp .env.template .env
nano .env
```

**Required settings in `.env`:**

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
MANAGEMENT_MODE=config_file  # or 'grpc'
```

### 4. Test the bot

```bash
# Activate virtual environment
source vless_bot_env/bin/activate

# Run test
python3 test_enhanced_vless_bot_simple.py
```

### 5. Start the bot service

```bash
# Start and enable the service
systemctl start vless-bot
systemctl enable vless-bot

# Check status
systemctl status vless-bot

# View logs
journalctl -u vless-bot -f
```

## 📁 Uploaded Files

The following files are now on your server at `/root/`:

### Core Bot Files:

- `vless_only_bot_enhanced.py` - Enhanced bot with dual management
- `vless_database.py` - Database functions
- `vless_config.py` - Server configuration
- `vless_utils.py` - gRPC utilities

### Supporting Files:

- `app/` - Protobuf files for gRPC
- `common/` - Common protobuf files
- `core/` - Core protobuf files

### Documentation & Testing:

- `ENHANCED_VLESS_BOT_README.md` - Comprehensive documentation
- `test_enhanced_vless_bot_simple.py` - Test script
- `setup_enhanced_vless_bot.sh` - Setup script

## 🔧 Management Modes

### Config File Mode (Recommended for your setup)

Since you have `init_server.py` set up, use config file mode:

```env
MANAGEMENT_MODE=config_file
```

This mode:

- Directly modifies `/usr/local/etc/xray/config.json`
- Works with your existing `init_server.py` setup
- Restarts Xray service after changes

### gRPC Mode (Alternative)

For dynamic user management via API:

```env
MANAGEMENT_MODE=grpc
```

This mode:

- Uses Xray's gRPC API
- Requires API configuration in Xray
- More dynamic but requires additional setup

## 🧪 Testing

Before running the full bot, test the components:

```bash
# Test database functions
python3 test_enhanced_vless_bot_simple.py

# Test with your existing setup
python3 init_server.py  # If not already done
```

## 📋 Bot Commands

Once deployed, users can use:

- `/start` - Welcome message
- `/help` - Show help
- `/vless_subscribe` - Get VLESS VPN access
- `/my_subscription` - Check subscription status

Admin commands:

- `/admin_remove <user_id>` - Remove user (admin only)

## 🔍 Troubleshooting

### Check service status:

```bash
systemctl status vless-bot
```

### View logs:

```bash
journalctl -u vless-bot -f
```

### Test database:

```bash
source vless_bot_env/bin/activate
python3 test_enhanced_vless_bot_simple.py
```

### Check Xray service:

```bash
systemctl status xray
```

## 🚨 Important Notes

1. **Backup your existing setup** before deploying
2. **Test thoroughly** with a small user group first
3. **Monitor logs** for any issues
4. **Keep your bot token secure**
5. **Ensure Xray service is running**

## 📞 Support

If you encounter issues:

1. Check the logs: `journalctl -u vless-bot -f`
2. Verify Xray is running: `systemctl status xray`
3. Test database functions
4. Check file permissions and paths

---

**Ready to deploy!** 🚀
