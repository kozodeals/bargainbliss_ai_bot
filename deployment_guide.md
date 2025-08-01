# BargainBliss AI Bot - Deployment Guide

## Secure Deployment Options

### Option 1: Cloud Server Deployment (Recommended)

#### **Platforms:**
- **DigitalOcean** ($5-10/month)
- **AWS EC2** ($10-20/month)
- **Google Cloud** ($10-20/month)
- **Vultr** ($5-10/month)
- **Heroku** (Free tier available)

#### **Steps:**

1. **Choose a Cloud Provider**
   ```bash
   # Example: DigitalOcean Droplet
   # 1. Create account at digitalocean.com
   # 2. Create a new droplet (Ubuntu 20.04)
   # 3. Connect via SSH
   ```

2. **Set Up Server**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3 python3-pip git -y
   
   # Install screen for background running
   sudo apt install screen -y
   ```

3. **Deploy Your Bot**
   ```bash
   # Clone your bot (or upload files)
   git clone https://github.com/yourusername/bargainbliss_ai_bot.git
   cd bargainbliss_ai_bot
   
   # Install dependencies
   pip3 install -r requirements.txt
   
   # Create .env file with your credentials
   nano .env
   ```

4. **Run Bot in Background**
   ```bash
   # Start a screen session
   screen -S bargainbliss_bot
   
   # Run the bot
   python3 bargainbliss_ai_bot.py
   
   # Detach from screen (Ctrl+A, then D)
   # Bot continues running in background
   ```

5. **Auto-restart on Server Reboot**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/bargainbliss-bot.service
   ```

   Add this content:
   ```ini
   [Unit]
   Description=BargainBliss AI Bot
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/bargainbliss_ai_bot
   ExecStart=/usr/bin/python3 /root/bargainbliss_ai_bot/bargainbliss_ai_bot.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

   Enable the service:
   ```bash
   sudo systemctl enable bargainbliss-bot.service
   sudo systemctl start bargainbliss-bot.service
   ```

### Option 2: Docker Deployment

#### **Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bargainbliss_ai_bot.py"]
```

#### **Deploy with Docker:**
```bash
# Build image
docker build -t bargainbliss-bot .

# Run container
docker run -d --name bargainbliss-bot \
  --env-file .env \
  --restart unless-stopped \
  bargainbliss-bot
```

### Option 3: Railway/Render (Easy Deployment)

#### **Railway:**
1. Connect your GitHub repo
2. Add environment variables in Railway dashboard
3. Deploy automatically

#### **Render:**
1. Connect your GitHub repo
2. Set environment variables
3. Deploy with one click

## Security Best Practices

### 1. **Environment Variables**
- Never commit `.env` file to Git
- Use cloud provider's secret management
- Rotate credentials regularly

### 2. **Access Control**
- Only you have server access
- Users only interact via Telegram
- No direct access to bot files

### 3. **Monitoring**
```bash
# Check bot status
sudo systemctl status bargainbliss-bot

# View logs
sudo journalctl -u bargainbliss-bot -f

# Restart if needed
sudo systemctl restart bargainbliss-bot
```

### 4. **Backup Strategy**
```bash
# Backup bot files
tar -czf bot-backup-$(date +%Y%m%d).tar.gz bargainbliss_ai_bot/

# Backup .env file separately
cp .env backup-env-$(date +%Y%m%d)
```

## User Access Control

### **What Users Can Do:**
- ✅ Send AliExpress URLs
- ✅ Receive affiliate links
- ✅ Use bot commands (/start, /help, /health)

### **What Users Cannot Do:**
- ❌ Access server files
- ❌ Modify bot settings
- ❌ Change API credentials
- ❌ Stop/restart the bot
- ❌ View logs or system info

## Cost Estimation

### **Monthly Costs:**
- **DigitalOcean Droplet**: $5-10/month
- **Domain (optional)**: $1-10/month
- **Total**: $6-20/month

### **Free Options:**
- **Railway**: Free tier available
- **Render**: Free tier available
- **Heroku**: Free tier available

## Maintenance

### **Regular Tasks:**
1. **Monitor logs** for errors
2. **Update dependencies** monthly
3. **Check API limits** and usage
4. **Backup data** weekly
5. **Monitor costs** monthly

### **Emergency Procedures:**
```bash
# Stop bot
sudo systemctl stop bargainbliss-bot

# Update code
git pull origin main

# Restart bot
sudo systemctl start bargainbliss-bot
```

## Scaling Considerations

### **When to Scale:**
- 100+ daily users
- High API usage
- Performance issues

### **Scaling Options:**
1. **Upgrade server** (more RAM/CPU)
2. **Load balancing** (multiple instances)
3. **Database** (for user tracking)
4. **CDN** (for static assets)

## Support & Monitoring

### **Monitoring Tools:**
- **Uptime Robot** (free uptime monitoring)
- **Telegram Bot API** (built-in analytics)
- **Server monitoring** (CPU, RAM, disk)

### **User Support:**
- Add `/support` command
- Create FAQ in bot
- Provide contact info for issues 