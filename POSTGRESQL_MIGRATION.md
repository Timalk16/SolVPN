# PostgreSQL Migration Guide

This guide will help you migrate your VPN bot from SQLite to PostgreSQL for better scalability and production readiness.

## Why PostgreSQL?

- **Better Performance**: Handles concurrent connections more efficiently
- **ACID Compliance**: Ensures data integrity
- **Advanced Features**: Better indexing, transactions, and query optimization
- **Production Ready**: Industry standard for production applications
- **Render Integration**: Native support on Render platform

## Files Added/Modified

### New Files:

- `database_postgresql.py` - PostgreSQL-specific database operations
- `migrate_to_postgresql.py` - Migration script to transfer data
- `deploy_postgresql.sh` - Deployment guide script
- `POSTGRESQL_MIGRATION.md` - This guide

### Modified Files:

- `database.py` - Now supports both SQLite and PostgreSQL
- `config.py` - Added PostgreSQL configuration options
- `requirements.txt` - Added `psycopg2-binary` dependency

## Setup Instructions

### 1. Local Development Setup

1. **Install PostgreSQL locally** (optional for development):

   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql

   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Create a local database** (optional):

   ```bash
   createdb vpn_bot
   ```

3. **Set environment variables**:

   ```bash
   # For local PostgreSQL
   export USE_POSTGRESQL=true
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=vpn_bot
   export POSTGRES_USER=your_username
   export POSTGRES_PASSWORD=your_password

   # Or use DATABASE_URL
   export DATABASE_URL=postgresql://user:password@localhost:5432/vpn_bot
   ```

### 2. Render Deployment Setup

1. **Create PostgreSQL database on Render**:

   - Go to your Render dashboard
   - Click "New" → "PostgreSQL"
   - Name: `vpn-bot-db`
   - Plan: Free (or paid for production)
   - Click "Create Database"

2. **Get the connection string**:

   - In your database dashboard, copy the "External Database URL"
   - It looks like: `postgresql://user:password@host:port/database`

3. **Configure your web service**:

   - Go to your `vpn-bot` web service
   - Add environment variables:
     - `DATABASE_URL`: [paste the connection string]
     - `USE_POSTGRESQL`: `true`

4. **Deploy**:
   - Push your code to trigger a new deployment
   - The application will automatically initialize the PostgreSQL database

### 3. Data Migration (Optional)

If you have existing data in SQLite that you want to transfer:

1. **Run the migration script**:

   ```bash
   python migrate_to_postgresql.py
   ```

2. **Verify the migration**:

   - The script will show counts from both databases
   - Check that all data was transferred correctly

3. **Test your application**:
   - Ensure all functionality works with PostgreSQL
   - Check that subscriptions, users, and payments work correctly

## Configuration Options

### Environment Variables

| Variable            | Description                       | Default        |
| ------------------- | --------------------------------- | -------------- |
| `USE_POSTGRESQL`    | Enable PostgreSQL (true/false)    | `true`         |
| `DATABASE_URL`      | Full PostgreSQL connection string | -              |
| `POSTGRES_HOST`     | PostgreSQL host                   | `localhost`    |
| `POSTGRES_PORT`     | PostgreSQL port                   | `5432`         |
| `POSTGRES_DB`       | Database name                     | `vpn_bot`      |
| `POSTGRES_USER`     | Database user                     | `vpn_bot_user` |
| `POSTGRES_PASSWORD` | Database password                 | -              |

### Priority Order

1. `DATABASE_URL` (highest priority)
2. Individual PostgreSQL variables
3. SQLite fallback (if `USE_POSTGRESQL=false`)

## Database Schema

The PostgreSQL schema is identical to SQLite but with PostgreSQL-specific optimizations:

### Tables:

- `users` - User information
- `subscriptions` - Subscription records
- `subscription_countries` - VPN keys for each country

### Indexes:

- `idx_subscriptions_user_id` - Fast user lookups
- `idx_subscriptions_status` - Fast status filtering
- `idx_subscriptions_end_date` - Fast expiration checks
- `idx_subscription_countries_subscription_id` - Fast country lookups

## Troubleshooting

### Common Issues

1. **Connection refused**:

   - Check if PostgreSQL is running
   - Verify connection string format
   - Ensure firewall allows connections

2. **Authentication failed**:

   - Verify username/password
   - Check database permissions

3. **Database not found**:

   - Create the database first
   - Check database name in connection string

4. **Migration errors**:
   - Ensure both SQLite and PostgreSQL are accessible
   - Check for data type conflicts
   - Verify table schemas match

### Debug Mode

Enable debug logging by setting:

```bash
export PYTHONPATH=.
python -c "from database import init_db; init_db()"
```

## Performance Benefits

- **Concurrent Connections**: PostgreSQL handles multiple simultaneous users better
- **Query Optimization**: Better query planner and indexing
- **Memory Management**: More efficient memory usage
- **Backup & Recovery**: Built-in backup and point-in-time recovery
- **Monitoring**: Better monitoring and performance metrics

## Production Considerations

1. **Connection Pooling**: Consider using connection pooling for high traffic
2. **Backup Strategy**: Set up automated backups
3. **Monitoring**: Monitor database performance and connections
4. **Scaling**: PostgreSQL can be easily scaled horizontally with read replicas
5. **Security**: Use SSL connections and proper authentication

## Rollback Plan

If you need to rollback to SQLite:

1. Set `USE_POSTGRESQL=false` in environment
2. Ensure SQLite database file exists
3. Restart the application

The application will automatically switch back to SQLite mode.

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Test database connectivity manually
4. Review the migration script output for any errors

## Next Steps

After successful migration:

1. Monitor application performance
2. Set up database backups
3. Consider implementing connection pooling
4. Add database monitoring and alerting
5. Plan for future scaling needs
