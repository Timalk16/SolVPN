# Render PostgreSQL Setup Guide

## Quick Setup Steps

### 1. Create PostgreSQL Database on Render

1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"PostgreSQL"**
3. Fill in the details:
   - **Name**: `vpn-bot-db`
   - **Plan**: Free (or paid for production)
   - **Region**: Choose closest to your users
4. Click **"Create Database"**

### 2. Get Database Connection String

1. In your new database dashboard, find **"External Database URL"**
2. Copy the connection string (looks like: `postgresql://user:password@host:port/database`)

### 3. Configure Your Web Service

1. Go to your `vpn-bot` web service
2. Click **"Environment"** tab
3. Add these environment variables:

   - **Key**: `DATABASE_URL`
   - **Value**: [paste the connection string from step 2]

   - **Key**: `USE_POSTGRESQL`
   - **Value**: `true`

### 4. Deploy

1. Push your code to trigger a new deployment
2. The application will automatically:
   - Install PostgreSQL dependencies
   - Initialize the database tables
   - Start using PostgreSQL

## Environment Variables Summary

Add these to your web service environment:

```
DATABASE_URL=postgresql://user:password@host:port/database
USE_POSTGRESQL=true
```

## Verification

After deployment, check your logs for:

- ✅ "PostgreSQL database initialized successfully"
- ✅ No database connection errors

## Troubleshooting

### If you see "cannot import name 'DB_PATH'" error:

- ✅ **FIXED** - This was resolved in the latest update

### If PostgreSQL connection fails:

1. Verify `DATABASE_URL` is correct
2. Check that the database is running
3. Ensure `USE_POSTGRESQL=true` is set

### If you want to fallback to SQLite:

1. Set `USE_POSTGRESQL=false` in environment
2. Restart the service

## Migration from SQLite (Optional)

If you have existing data in SQLite:

1. Download your SQLite database file
2. Run locally: `python migrate_to_postgresql.py`
3. Verify data transfer
4. Deploy to Render

## Support

- Check Render logs for detailed error messages
- Verify all environment variables are set correctly
- Test database connectivity manually if needed
