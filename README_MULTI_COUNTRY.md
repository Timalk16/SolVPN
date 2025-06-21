# Multi-Country VPN Bot Setup

This VPN bot now supports multiple countries with different subscription packages. Users can subscribe to plans that include access to 5 countries (usual package) or 10 countries (large package).

## New Features

### Multi-Country Support

- **Germany** 🇩🇪 - Available in all plans
- **France** 🇫🇷 - Available in all plans
- Easy to extend with more countries

### Subscription Plans

- **Test Plan**: 5 minutes, Germany only - 0.1 USDT
- **5 Countries Package**:
  - 1 Month - 2.0 USDT
  - 3 Months - 5.0 USDT
  - 1 Year - 15.0 USDT
- **10 Countries Package**:
  - 1 Month - 3.5 USDT
  - 3 Months - 8.5 USDT
  - 1 Year - 25.0 USDT

## Configuration

### Environment Variables

Update your `.env` file with the following variables:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_ID=your_admin_user_id_here

# Outline VPN Server Configuration for Multiple Countries
# Germany Server
OUTLINE_API_URL_GERMANY=https://your-germany-server.com:port/api
OUTLINE_CERT_SHA256_GERMANY=your_germany_server_cert_sha256_here

# France Server
OUTLINE_API_URL_FRANCE=https://your-france-server.com:port/api
OUTLINE_CERT_SHA256_FRANCE=your_france_server_cert_sha256_here

# Legacy support (if you have an old single server config)
# OUTLINE_API_URL=https://your-old-server.com:port/api
# OUTLINE_CERT_SHA256=your_old_server_cert_sha256_here

# Payment Gateway Configuration
YOOKASSA_SHOP_ID=your_yookassa_shop_id_here
YOOKASSA_SECRET_KEY=your_yookassa_secret_key_here

# CryptoBot API Configuration
CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_testnet_token_here
CRYPTOBOT_MAINNET_API_TOKEN=your_cryptobot_mainnet_token_here
```

### Adding More Countries

To add more countries, update the `OUTLINE_SERVERS` configuration in `config.py`:

```python
OUTLINE_SERVERS = {
    "germany": {
        "api_url": os.getenv("OUTLINE_API_URL_GERMANY"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_GERMANY", ""),
        "name": "Germany",
        "flag": "🇩🇪"
    },
    "france": {
        "api_url": os.getenv("OUTLINE_API_URL_FRANCE"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_FRANCE", ""),
        "name": "France",
        "flag": "🇫🇷"
    },
    # Add new countries here
    "netherlands": {
        "api_url": os.getenv("OUTLINE_API_URL_NETHERLANDS"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_NETHERLANDS", ""),
        "name": "Netherlands",
        "flag": "🇳🇱"
    }
}
```

Then update the `PLANS` configuration to include the new countries:

```python
PLANS = {
    "1_month_5_countries": {
        "name": "1 Month (5 Countries)",
        "duration_days": 30,
        "price_usdt": 2.0,
        "countries": ["germany", "france", "netherlands"]  # Add new countries
    }
}
```

## Database Changes

The database schema has been updated to support multiple countries:

### New Table: `subscription_countries`

- Links subscriptions to countries and their VPN keys
- Stores `outline_key_id` and `outline_access_url` for each country

### Updated Table: `subscriptions`

- Removed `outline_key_id` and `outline_access_url` columns
- VPN keys are now stored in the `subscription_countries` table

## User Experience

### Subscription Flow

1. User selects a plan (shows available countries)
2. User makes payment
3. System creates VPN keys for each country in the plan
4. User receives access keys for all countries

### My Subscriptions

- Shows all active subscriptions
- Displays countries and their respective VPN keys
- Users can copy keys for each country

### Admin Functions

- Admin can view all subscriptions with country information
- Admin can delete subscriptions (removes all VPN keys for all countries)
- Admin can see which countries are included in each subscription

## Migration from Single Country

If you're upgrading from the single-country version:

1. **Backup your database** before running the new version
2. **Update your environment variables** with the new multi-country configuration
3. **Run the bot** - the database will be automatically updated with the new schema
4. **Existing subscriptions** will continue to work but will only show the legacy country

## Testing

To test the multi-country functionality:

1. Run `python outline_utils.py` to test connections to all configured servers
2. Use the test plan to verify VPN key creation for Germany
3. Test a 5-country plan to verify multiple key creation
4. Check that `/my_subscriptions` displays all countries correctly

## Troubleshooting

### Common Issues

1. **"Country not found in OUTLINE_SERVERS configuration"**

   - Check that the country code in your plan matches the keys in `OUTLINE_SERVERS`

2. **"Failed to create any VPN keys"**

   - Verify that all Outline servers are accessible
   - Check API URLs and certificates

3. **Database errors**
   - Ensure you've backed up your database before upgrading
   - The new schema will be created automatically

### Adding a New Country

1. Set up an Outline server in the new country
2. Add the server configuration to `OUTLINE_SERVERS`
3. Add the country to the appropriate plans in `PLANS`
4. Update your `.env` file with the new server details
5. Restart the bot

## Future Enhancements

- Country selection by users (let users choose which countries they want)
- Geographic load balancing
- Country-specific pricing
- Automatic failover between countries
