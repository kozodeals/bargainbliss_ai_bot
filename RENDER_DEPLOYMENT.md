# 🚀 Render Deployment Guide

## **Step-by-Step Render Setup**

### **1. Service Type Selection**

When you're on Render and logged in through GitHub, you'll see several service types. Choose:

**✅ Web Service** (Recommended)
- This is the correct choice for your Telegram bot
- Provides continuous running service
- Handles background processes well

**❌ Don't choose:**
- Static Site (for websites)
- Background Worker (limited features)
- Cron Job (scheduled tasks only)

### **2. Connect Your Repository**

1. **Click "New +"** button
2. **Select "Web Service"**
3. **Connect your GitHub repository**
4. **Select your `bargainbliss_ai_bot` repository**

### **3. Configure Your Service**

#### **Basic Settings:**
- **Name**: `bargainbliss-ai-bot` (or any name you prefer)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)

#### **Build Command:**
```bash
pip install -r requirements.txt
```

#### **Start Command:**
```bash
python bargainbliss_ai_bot.py
```

### **4. Add Environment Variables**

Click on "Environment" tab and add these variables:

```
TELEGRAM_TOKEN=8253966352:AAE9c0k2kwsYt3kK9DYJ83IW5nHl3QImmy8
ALIEXPRESS_API_KEY=515878
ALIEXPRESS_SECRET_KEY=MbbuLsPwmjzA65DPnsK8KDfYIEI9jl1C
TRACKING_ID=bargainbliss_ai_bot
```

### **5. Advanced Settings (Optional)**

#### **Auto-Deploy:**
- ✅ **Enable** - Deploys automatically when you push to GitHub

#### **Health Check Path:**
- Leave empty (not needed for Telegram bots)

#### **Instance Type:**
- **Free** - Perfect for starting out

### **6. Deploy**

1. **Click "Create Web Service"**
2. **Wait for deployment** (2-5 minutes)
3. **Check logs** for any errors
4. **Test your bot** on Telegram

## **Troubleshooting**

### **Common Issues:**

#### **Build Fails:**
- Check that `requirements.txt` exists
- Ensure all dependencies are listed
- Check Python version compatibility

#### **Bot Not Responding:**
- Check environment variables are set correctly
- Verify Telegram token is valid
- Check logs for error messages

#### **Service Stops:**
- Free tier has limitations
- Service may sleep after inactivity
- Upgrade to paid plan for 24/7 uptime

## **Monitoring Your Bot**

### **Render Dashboard:**
- **Logs**: Real-time deployment and runtime logs
- **Metrics**: CPU, memory usage
- **Deployments**: History of all deployments
- **Environment**: Manage environment variables

### **Useful Commands in Logs:**
```bash
# Check if bot started successfully
"Bot started successfully!"

# Check for errors
"ERROR" or "Exception"

# Check API connection
"API connection successful"
```

## **Free Tier Limits**

- ✅ **750 hours/month** free
- ✅ **Automatic deployments**
- ✅ **Custom domains**
- ⚠️ **Service may sleep** after inactivity
- ⚠️ **Limited resources** (512MB RAM)

## **Upgrading (When Needed)**

### **When to Upgrade:**
- 100+ daily users
- High API usage
- Need 24/7 uptime
- Performance issues

### **Paid Plans:**
- **Starter**: $7/month (always on)
- **Standard**: $25/month (more resources)
- **Pro**: $50/month (enterprise features)

## **Next Steps After Deployment**

1. **Test your bot** on Telegram
2. **Share with friends** for testing
3. **Monitor logs** for any issues
4. **Scale up** if needed

## **Useful Render Commands**

### **Check Service Status:**
- Go to your service dashboard
- Check "Events" tab for deployment status
- Check "Logs" tab for runtime logs

### **Redeploy:**
- Click "Manual Deploy" button
- Or push new code to GitHub (auto-deploy)

### **Update Environment Variables:**
- Go to "Environment" tab
- Edit variables as needed
- Service restarts automatically

## **Success Indicators**

✅ **Deployment successful** when you see:
- "Build completed successfully"
- "Bot started successfully!" in logs
- No error messages

✅ **Bot working** when:
- Bot responds to `/start` command
- Bot accepts AliExpress URLs
- Bot generates affiliate links

## **Support**

If you encounter issues:
1. **Check Render logs** first
2. **Verify environment variables**
3. **Test locally** to ensure code works
4. **Contact Render support** if needed

Your bot should be live in 5-10 minutes! 🎉 