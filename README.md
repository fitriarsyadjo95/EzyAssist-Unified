# 🚀 EzyAssist Unified System

A complete Telegram bot and web registration system combined into a single application.

## 📋 Features

- **🤖 Telegram Bot**: AI-powered forex conversation bot
- **📝 Web Registration**: Beautiful multi-step registration forms
- **💾 Database Integration**: PostgreSQL support for user data
- **🔒 Security**: JWT tokens, rate limiting, input validation
- **📱 Responsive**: Mobile-first design
- **⚡ FastAPI**: High-performance async web framework

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                EzyAssist Unified                    │
├─────────────────────────────────────────────────────┤
│  FastAPI Application (main.py)                     │
│  ├── Telegram Bot Routes                           │
│  │   ├── /telegram_webhook                         │
│  │   ├── Bot Commands (/start, /register, /clear)  │
│  │   └── Message Handling                          │
│  ├── Web Registration Routes                       │
│  │   ├── / (registration form)                     │
│  │   ├── /submit (form processing)                 │
│  │   └── /success (confirmation)                   │
│  ├── API Endpoints                                 │
│  │   ├── /health (system status)                   │
│  │   └── /api/register (external API)              │
│  └── Database Models                               │
│      └── VipRegistration (PostgreSQL)              │
└─────────────────────────────────────────────────────┘
```

## 🔧 Components

### Core Files
- `main.py` - Main FastAPI application with all routes
- `conversation_engine.py` - AI conversation handling
- `supabase_client.py` - Database client for conversation data
- `broker_profiles.py` - Broker information data
- `broker_training_data.py` - Training data for AI

### Templates & Assets
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JavaScript, and images

### Configuration
- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- `.replit` - Replit deployment config

## 🚀 Quick Start

### 1. Environment Setup
Copy `.env.example` to `.env` and configure:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_URL=https://your-app.repl.co
ADMIN_ID=your_telegram_id

# OpenAI
OPENAI_API_KEY=your_openai_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Database (auto-provided by Replit)
DATABASE_URL=postgresql://...

# Security
JWT_SECRET_KEY=your_64_char_secret_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python main.py
```

### 4. Set Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://your-app.repl.co/telegram_webhook"}'
```

## 📱 Usage

### For Users
1. **Start Bot**: Send `/start` to your Telegram bot
2. **Register**: Send `/register` to get registration link
3. **Fill Form**: Complete the web registration form
4. **Get Confirmation**: Receive confirmation via Telegram

### For Developers
1. **Health Check**: `GET /health`
2. **Registration API**: `POST /api/register`
3. **Webhook Test**: `GET /webhook-test`

## 🔄 User Flow

```
User → /start → Bot Welcome
     ↓
User → /register → Registration Token Generated
     ↓
User → Clicks Link → Web Form
     ↓
User → Submits Form → Data Saved
     ↓
User → Gets Confirmation → Bot Message
```

## 🛠️ Development

### Project Structure
```
EzyAssist-Unified/
├── main.py                 # Main FastAPI application
├── conversation_engine.py  # AI conversation handling
├── supabase_client.py     # Database client
├── broker_profiles.py     # Broker data
├── broker_training_data.py # AI training data
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html         # Registration form
│   ├── success.html       # Success page
│   └── error.html         # Error page
├── static/               # Static assets
│   ├── css/
│   └── js/
├── requirements.txt      # Dependencies
├── .replit              # Deployment config
└── .env.example         # Environment template
```

### Key Functions
- `generate_registration_token()` - Create secure JWT tokens
- `verify_registration_token()` - Validate and decode tokens
- `send_registration_confirmation()` - Bot notifications
- `send_admin_notification()` - Admin alerts

## 📊 Database Schema

### VipRegistration Table
```sql
CREATE TABLE vip_registrations (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR NOT NULL,
    telegram_username VARCHAR,
    full_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    brokerage_name VARCHAR,
    deposit_amount VARCHAR,
    client_id VARCHAR,
    ip_address VARCHAR,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 Security Features

- **JWT Tokens**: Secure registration links with expiration
- **Input Validation**: Server-side form validation
- **Rate Limiting**: Prevent spam submissions
- **HTTPS Only**: Secure communication
- **SQL Injection Prevention**: Parameterized queries

## 🚀 Deployment on Replit

### 1. Create Project
1. Go to Replit.com
2. Create new project: "EzyAssist Unified"
3. Upload all files from this folder

### 2. Enable Database
1. Click Database tab in Replit
2. Enable PostgreSQL
3. DATABASE_URL will be auto-provided

### 3. Set Environment Variables
Add these to Replit Secrets:
- All variables from `.env.example`
- Use your actual values

### 4. Deploy
1. Click Deploy tab
2. Choose "Autoscale deployment"
3. Click Deploy
4. Note your app URL

### 5. Configure Webhook
Set your Telegram webhook to your Replit URL:
```bash
https://your-app.repl.co/telegram_webhook
```

## 📈 Monitoring

### Health Checks
- `GET /health` - System status
- Check logs in Replit console
- Monitor database usage

### Metrics to Track
- User registrations per day
- Bot message volume
- Error rates
- Response times

## 🔧 Troubleshooting

### Common Issues

**Bot not responding:**
- Check `TELEGRAM_BOT_TOKEN`
- Verify webhook URL is set
- Check Replit logs for errors

**Form submissions failing:**
- Verify `DATABASE_URL` is set
- Check PostgreSQL is enabled
- Validate `JWT_SECRET_KEY`

**Database errors:**
- Ensure PostgreSQL is enabled in Replit
- Check table exists (auto-created on startup)
- Verify connection string format

### Debugging Commands
```bash
# Check webhook info
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Test health endpoint
curl https://your-app.repl.co/health

# Test webhook endpoint
curl https://your-app.repl.co/webhook-test
```

## 💰 Cost Estimate

**Replit Pricing:**
- Free tier: Limited hours
- Always On: $7/month (recommended for production)
- Database: Included with subscription

**Total: ~$7/month for production use**

## 🆚 Benefits vs Separate Systems

| Feature | Unified System | Separate Systems |
|---------|---------------|------------------|
| **Cost** | $7/month | $14/month |
| **Deployment** | 1 project | 2 projects |
| **Communication** | Direct functions | HTTP webhooks |
| **Debugging** | Single log | Multiple logs |
| **Maintenance** | Easier | More complex |
| **Performance** | Faster | Network latency |

## 📞 Support

If you encounter issues:
1. Check this README
2. Review Replit console logs
3. Test individual endpoints
4. Verify environment variables

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ `/health` returns OK status
- ✅ Bot responds to `/start` command
- ✅ `/register` generates working form links
- ✅ Form submissions save to database
- ✅ Users receive confirmation messages
- ✅ Admin receives registration notifications

---

**Built with ❤️ for Malaysian forex traders**