# 🚀 VLESS Integration Guide

This guide explains how to integrate VLESS VPN functionality into your main Telegram bot while keeping the existing Outline functionality intact.

## 📋 **Overview**

### **Architecture:**

- **Main Bot (Render)**: Handles payments, user management, and Outline subscriptions
- **VPS (77.110.110.205)**: Runs VLESS bot and Xray server
- **API Bridge**: Enables communication between main bot and VPS

### **New Commands:**

- `/vless_subscribe` - Purchase VLESS VPN subscription with payment
- `/vless_status` - Check VLESS subscription status
- Menu buttons for both Outline and VLESS options

---

## 🛠️ **Step 1: Deploy VPS API Bridge**

### **1.1 Upload and Run Deployment Script**

```bash
# Upload deployment script to VPS
scp deploy_vps_api.sh root@77.110.110.205:/root/

# SSH into VPS and run deployment
ssh root@77.110.110.205
chmod +x deploy_vps_api.sh
./deploy_vps_api.sh
```

### **1.2 Verify API Bridge**

```bash
# Test API health
curl http://77.110.110.205:5000/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-01-XX..."}
```

### **1.3 Get API Credentials**

The deployment script will output:

```
✅ VPS API Bridge deployed successfully!
📋 API Key: your-secret-api-key-1234567890
🌐 API URL: http://77.110.110.205:5000
```

**Save these credentials for the next step!**

---

## 🚀 **Step 2: Update Main Bot Environment**

### **2.1 Add Environment Variables**

Add these to your main bot's `.env` file on Render:

```env
# VPS API Configuration
VPS_API_URL=http://77.110.110.205:5000
VPS_API_KEY=your-secret-api-key-1234567890
```

### **2.2 Update Requirements**

The `requirements.txt` file has been updated with:

```
httpx>=0.24.0
flask-cors>=4.0.0
```

---

## 🔧 **Step 3: Deploy Updated Main Bot**

### **3.1 Files Modified:**

1. **`main.py`** - Added VLESS commands and conversation handlers
2. **`vps_api_client.py`** - New file for VPS communication
3. **`requirements.txt`** - Added new dependencies

### **3.2 New Features:**

- **VLESS Subscription Flow**: Full payment integration
- **VLESS Status Checking**: Real-time subscription status
- **Menu Integration**: Both Outline and VLESS options
- **Error Handling**: Robust error handling for API communication

---

## 📱 **Step 4: Test the Integration**

### **4.1 Test Commands:**

1. **Start the bot**: `/start`

   - Should show both Outline and VLESS options

2. **Test VLESS subscription**: `/vless_subscribe`

   - Should show VLESS duration plans
   - Should process payments
   - Should create VLESS user on VPS

3. **Test VLESS status**: `/vless_status`
   - Should show current VLESS subscription
   - Should display VLESS URI

### **4.2 Test Payment Flow:**

1. Choose VLESS duration plan
2. Select payment method (card/crypto)
3. Complete payment
4. Verify VLESS user creation on VPS
5. Check VLESS URI generation

---

## 🔍 **Step 5: Monitor and Debug**

### **5.1 Check VPS API Logs:**

```bash
ssh root@77.110.110.205
journalctl -u vps-api -f
```

### **5.2 Check Main Bot Logs:**

Monitor your Render deployment logs for:

- API communication errors
- Payment processing issues
- VLESS user creation status

### **5.3 Test API Endpoints:**

```bash
# Health check
curl http://77.110.110.205:5000/health

# Add user (with API key)
curl -X POST http://77.110.110.205:5000/vless/add_user \
  -H "Authorization: Bearer your-secret-api-key-1234567890" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456, "duration_days": 30}'

# Get user status
curl "http://77.110.110.205:5000/vless/user_status?user_id=123456" \
  -H "Authorization: Bearer your-secret-api-key-1234567890"
```

---

## 🎯 **Step 6: User Migration Strategy**

### **6.1 Announcement to Users:**

```
🚀 Новое обновление!

Добавлена поддержка VLESS VPN с протоколом REALITY для максимальной безопасности и скорости.

Теперь доступны два варианта:
🟢 Outline VPN - проверенное решение
🚀 VLESS VPN - новое поколение VPN

Попробуйте /vless_subscribe для тестирования!
```

### **6.2 Migration Incentives:**

- **Free Trial**: Offer 7 days free VLESS for existing users
- **Better Performance**: Highlight REALITY protocol benefits
- **Enhanced Security**: Emphasize VLESS security features

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **API Connection Timeout**

   - Check VPS firewall settings
   - Verify API port (5000) is open
   - Check nginx configuration

2. **Authentication Errors**

   - Verify API key in environment variables
   - Check API key format (Bearer token)

3. **VLESS User Creation Fails**

   - Check Xray service status on VPS
   - Verify config.json permissions
   - Check VPS disk space

4. **Payment Processing Issues**
   - Verify payment gateway configuration
   - Check payment verification logic
   - Monitor payment logs

### **Debug Commands:**

```bash
# Check VPS services
systemctl status vps-api
systemctl status xray
systemctl status nginx

# Check VPS logs
journalctl -u vps-api -n 50
journalctl -u xray -n 50

# Test Xray configuration
/usr/local/bin/xray -test -config /usr/local/etc/xray/config.json
```

---

## 📊 **Monitoring**

### **Key Metrics to Monitor:**

1. **API Response Times**: Should be < 5 seconds
2. **Payment Success Rate**: Should be > 95%
3. **VLESS User Creation Success**: Should be > 98%
4. **User Adoption Rate**: Track VLESS vs Outline usage

### **Log Analysis:**

```bash
# Monitor API requests
tail -f /var/log/nginx/access.log | grep vps-api

# Monitor VLESS operations
grep "VLESS" /var/log/syslog
```

---

## 🔄 **Future Enhancements**

### **Phase 2 Features:**

1. **User Preference System**: Let users choose default protocol
2. **Migration Tools**: Help users switch between protocols
3. **Advanced Analytics**: Track usage patterns
4. **Multi-Server Support**: Add more VLESS servers

### **Phase 3 Features:**

1. **Automatic Migration**: Gradually move users to VLESS
2. **Protocol Comparison**: Show speed/security differences
3. **Advanced Management**: Admin tools for protocol management

---

## 📞 **Support**

If you encounter issues:

1. **Check logs** on both Render and VPS
2. **Test API endpoints** manually
3. **Verify environment variables** are set correctly
4. **Contact support** with specific error messages

---

## ✅ **Success Criteria**

The integration is successful when:

- ✅ Users can purchase VLESS subscriptions with payment
- ✅ VLESS users are created on VPS automatically
- ✅ VLESS URIs are generated and sent to users
- ✅ Both Outline and VLESS coexist without conflicts
- ✅ API communication is reliable and fast
- ✅ Error handling works for all edge cases

---

**🎉 Congratulations! You now have a fully integrated VLESS VPN system alongside your existing Outline VPN service!**
