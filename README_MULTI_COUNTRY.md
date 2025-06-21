# Multi-Country VPN Bot - Enhanced User Flow

This document describes the enhanced multi-country VPN bot with an improved user experience flow.

## New User Flow: Duration → Payment → Countries

The bot now follows a more user-friendly flow:

1. **User chooses duration** (1 month, 3 months, 1 year)
2. **User pays** for the selected duration
3. **User chooses countries** after successful payment

This flow is more comfortable because:

- Users know the total cost upfront
- They can focus on one decision at a time
- They can choose countries based on their needs after payment
- It's more intuitive and less overwhelming

## Configuration

### Duration Plans (`config.py`)

```python
DURATION_PLANS = {
    "test_5min": {
        "name": "Test (5 min)",
        "duration_days": 0.00347,
        "price_usdt": 0.1
    },
    "1_month": {
        "name": "1 Month",
        "duration_days": 30,
        "price_usdt": 2.0
    },
    "3_months": {
        "name": "3 Months",
        "duration_days": 90,
        "price_usdt": 5.0
    },
    "1_year": {
        "name": "1 Year",
        "duration_days": 365,
        "price_usdt": 15.0
    }
}
```

### Country Packages (`config.py`)

```python
COUNTRY_PACKAGES = {
    "5_countries": {
        "name": "5 Countries Package",
        "countries": ["germany", "france"],  # Will be extended as more countries are added
        "description": "Access to 5 different countries"
    },
    "10_countries": {
        "name": "10 Countries Package",
        "countries": ["germany", "france"],  # Will be extended to 10 countries
        "description": "Access to 10 different countries"
    }
}
```

### Outline Servers (`config.py`)

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
    }
}
```

## Database Schema

### Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    duration_plan_id TEXT,           -- References DURATION_PLANS
    country_package_id TEXT,         -- References COUNTRY_PACKAGES
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    status TEXT DEFAULT 'pending_payment',
    payment_id TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
```

### Subscription Countries Table

```sql
CREATE TABLE subscription_countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER,
    country_code TEXT,               -- e.g., 'germany', 'france'
    outline_key_id TEXT,
    outline_access_url TEXT,
    FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
);
```

## User Experience Flow

### 1. Duration Selection

```
User: /subscribe
Bot: "Please choose a subscription duration:"
     [Test (5 min) - 0.10 USDT]
     [1 Month - 2.00 USDT]
     [3 Months - 5.00 USDT]
     [1 Year - 15.00 USDT]
     [❌ Cancel]
```

### 2. Payment

```
User: Selects "1 Month"
Bot: "You've selected: 1 Month
     Price: 2.00 USDT.

     Please choose your payment method:"
     [💰 Pay 2.00 USDT (Crypto)]
     [⬅️ Back to Duration]
```

### 3. Country Selection (After Payment)

```
User: Completes payment
Bot: "✅ Payment successful!

     Duration: 1 Month
     Price: 2.00 USDT

     Now choose your country package:"
     [5 Countries Package - Access to 5 different countries]
     [10 Countries Package - Access to 10 different countries]
     [❌ Cancel]
```

### 4. Subscription Activation

```
User: Selects "5 Countries Package"
Bot: "🎉 Your VPN subscription is now active!

     Duration: 1 Month
     Package: 5 Countries Package
     Countries: 🇩🇪 Germany, 🇫🇷 France
     Expires: 2024-01-15 14:30:00

     Use /my_subscriptions to get your VPN access keys."
```

## Key Features

### Multi-Country Support

- Users can access VPN servers in multiple countries
- Each country has its own Outline server configuration
- VPN keys are created per country per subscription

### Flexible Duration Plans

- Separate duration plans from country packages
- Easy to add new duration options
- Clear pricing upfront

### Country Packages

- Predefined country combinations
- Easy to extend with more countries
- Clear descriptions for users

### Enhanced User Experience

- Step-by-step flow reduces cognitive load
- Users know total cost before payment
- Country selection after payment allows for better decision making

## Migration from Old Schema

If you're upgrading from the old single-country schema, use the migration script:

```bash
python migrate_to_multi_country.py
```

This will:

1. Create new tables with the updated schema
2. Migrate existing subscriptions to the new format
3. Preserve all user data and VPN keys

## Adding New Countries

1. **Add server configuration** to `OUTLINE_SERVERS` in `config.py`
2. **Update country packages** to include the new country
3. **Set environment variables** for the new server
4. **Test the new country** with a test subscription

Example adding Netherlands:

```python
OUTLINE_SERVERS = {
    # ... existing countries ...
    "netherlands": {
        "api_url": os.getenv("OUTLINE_API_URL_NETHERLANDS"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_NETHERLANDS", ""),
        "name": "Netherlands",
        "flag": "🇳🇱"
    }
}

COUNTRY_PACKAGES = {
    "5_countries": {
        "name": "5 Countries Package",
        "countries": ["germany", "france", "netherlands"],
        "description": "Access to 5 different countries"
    }
    # ... other packages ...
}
```

## Environment Variables

Add these to your `.env` file:

```env
# Germany Server
OUTLINE_API_URL_GERMANY=https://your-germany-server.com/api
OUTLINE_CERT_SHA256_GERMANY=your-germany-cert-sha256

# France Server
OUTLINE_API_URL_FRANCE=https://your-france-server.com/api
OUTLINE_CERT_SHA256_FRANCE=your-france-cert-sha256

# Add more countries as needed
OUTLINE_API_URL_NETHERLANDS=https://your-netherlands-server.com/api
OUTLINE_CERT_SHA256_NETHERLANDS=your-netherlands-cert-sha256
```

## Benefits of the New Flow

1. **Better User Experience**: Users make decisions one at a time
2. **Clearer Pricing**: Total cost is known before payment
3. **Flexible Country Selection**: Users can choose countries based on their needs
4. **Easier Management**: Separate duration and country configurations
5. **Scalable**: Easy to add new countries and duration plans
6. **Reduced Confusion**: Less overwhelming for new users

## Testing

The new flow has been tested and verified to work correctly. The database schema supports:

- Pending subscriptions (duration only)
- Active subscriptions (duration + countries)
- Multiple VPN keys per subscription
- Proper cleanup and expiration handling

## Support

For issues or questions about the new multi-country flow, check:

1. Database schema matches the expected format
2. Environment variables are set correctly
3. Outline servers are accessible
4. Payment gateway is working properly
