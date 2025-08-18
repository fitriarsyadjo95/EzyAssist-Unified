# 🚀 EzyAssist Unified System - Deployment Guide

## 📋 Pre-Deployment Checklist

- [ ] Telegram Bot Token from @BotFather
- [ ] OpenAI API Key
- [ ] Supabase Project (URL + Anon Key)  
- [ ] Admin Telegram User ID
- [ ] JWT Secret Key (64 characters)
- [ ] Replit account ready

---

## 🔧 Step 1: Create Replit Project

1. **Go to [Replit.com](https://replit.com)**
2. **Click "Create Repl"**
3. **Choose "Import from GitHub" or "Upload files"**
4. **Name:** `ezyassist-unified-system`

---

## 📁 Step 2: Upload Files

Upload all files from the `EzyAssist-Unified/` folder:

```
📁 Root Directory
├── main.py
├── conversation_engine.py
├── supabase_client.py
├── broker_profiles.py
├── broker_training_data.py
├── requirements.txt
├── pyproject.toml
├── .replit
├── .env.example
└── 📁 templates/
    ├── base.html
    ├── index.html
    ├── success.html
    └── error.html
└── 📁 static/
    ├── 📁 css/
    └── 📁 js/
```

---

## 🗄️ Step 3: Enable Database

1. **Click Database tab** on left sidebar
2. **Enable PostgreSQL**
3. **Replit will auto-provide** `DATABASE_URL`

---

## 🔐 Step 4: Configure Environment Variables

In **Replit Secrets** (🔒 tab), add these variables:

### Required Variables
```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_WEBHOOK_URL=https://your-repl-name.username.repl.co
ADMIN_ID=your_telegram_user_id

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Security Keys
JWT_SECRET_KEY=your_64_character_secret_key_here
SESSION_SECRET=your_session_secret_here

# Application Settings
BASE_URL=https://your-repl-name.username.repl.co
PORT=8000
LOG_LEVEL=INFO
```

### Auto-Provided by Replit
```bash
DATABASE_URL=postgresql://... (auto-provided)
```

---

## 🚀 Step 5: Deploy

1. **Click "Deploy" tab**
2. **Choose "Autoscale deployment"**
3. **Click "Deploy"**
4. **Wait for deployment to complete**
5. **Note your deployment URL:** `https://your-repl-name.username.repl.co`

---

## 🤖 Step 6: Configure Telegram Webhook

Set your Telegram bot webhook to point to your Replit app:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://your-repl-name.username.repl.co/telegram_webhook"}'
```

**Replace:**
- `<YOUR_BOT_TOKEN>` with your actual bot token
- `your-repl-name.username.repl.co` with your actual Replit URL

---

## ✅ Step 7: Test Your Deployment

### 7.1 Test System Health
Visit: `https://your-repl-name.username.repl.co/health`

Should show:
```json
{
  "status": "ok",
  "message": "EzyAssist Unified System is running",
  "bot_ready": true,
  "database_ready": true
}
```

### 7.2 Test Telegram Bot
1. **Find your bot** on Telegram
2. **Send `/start`** - should get welcome message  
3. **Send `/register`** - should get registration link
4. **Click the link** - should open registration form

### 7.3 Test Registration Flow
1. **Complete registration form**
2. **Submit form**
3. **Should receive confirmation** on Telegram
4. **Admin should get notification**

---

## 🛠️ Troubleshooting

### ❌ "Internal Server Error"
**Check:** Replit Console logs for specific errors
**Fix:** Verify all environment variables are set correctly

### ❌ Bot not responding
**Check:** 
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
**Fix:** Ensure webhook URL is correctly set

### ❌ Database connection errors
**Check:** PostgreSQL is enabled in Replit Database tab
**Fix:** Restart your Repl to refresh database connection

### ❌ Registration form errors
**Check:** JWT_SECRET_KEY is set and 64+ characters
**Fix:** Generate new secret key if needed

---

## 📊 Step 8: Enable Production Features

### 8.1 Always On (Recommended)
- **Go to:** Your Repl → "Always On" tab
- **Enable:** Always On ($7/month)
- **Benefit:** 24/7 uptime for your bot

### 8.2 Custom Domain (Optional)
- **Go to:** Deploy tab → Custom Domain
- **Add:** Your custom domain
- **Update:** Environment variables with new domain

---

## 🔍 Monitoring Your System

### Key Metrics to Watch
- **Response Time:** Check `/health` endpoint speed
- **Error Rate:** Monitor Replit console for errors  
- **User Activity:** Track registrations in database
- **Bot Messages:** Monitor Telegram message volume

### Health Check Endpoints
```bash
# System health
GET https://your-app.repl.co/health

# Webhook test  
GET https://your-app.repl.co/webhook-test

# Telegram webhook status
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## 🎯 Success Checklist

Your deployment is successful when:

- [ ] ✅ Health endpoint returns OK
- [ ] ✅ Bot responds to `/start` command
- [ ] ✅ `/register` generates working links
- [ ] ✅ Registration form loads properly
- [ ] ✅ Form submissions save to database
- [ ] ✅ Users receive confirmation messages
- [ ] ✅ Admin receives registration notifications
- [ ] ✅ No errors in Replit console logs

---

## 💰 Cost Summary

| Feature | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Hosting** | Limited hours | $7/month (Always On) |
| **Database** | 1GB | Unlimited |
| **Custom Domain** | ❌ | ✅ |
| **24/7 Uptime** | ❌ | ✅ |

**Recommended for production:** $7/month with Always On

---

## 🆘 Need Help?

1. **Check this guide** for common issues
2. **Review Replit console logs** for specific errors
3. **Test individual endpoints** to isolate problems
4. **Verify environment variables** are correctly set

---

## 🎉 You're Live!

Once deployed successfully, your unified system provides:

- **🤖 AI-powered Telegram bot** for forex education
- **📝 Beautiful registration forms** for VIP signup  
- **💾 Secure database storage** for user data
- **📱 Mobile-responsive design** for all devices
- **🔒 Enterprise-grade security** with JWT tokens

**Total setup time:** ~30 minutes
**Monthly cost:** $7 (with Always On)
**Users supported:** Unlimited

Your Malaysian forex education platform is now live! 🇲🇾📈