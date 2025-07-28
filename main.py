#!/usr/bin/env python3
"""
EzyAssist Unified System - Combines Telegram Bot and Registration Form
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
import time
from functools import wraps

# FastAPI and web components
from fastapi import FastAPI, Request, Form, HTTPException, status, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Telegram bot components
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Database and external services
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import requests
import uvicorn

# AI and conversation
from conversation_engine import ConversationEngine
from supabase_client import SupabaseClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="EzyAssist Unified System", version="1.0.0")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    engine = None
    SessionLocal = None
    Base = None
    logger.warning("Database URL not configured - running without database")

# Database Models
if Base:
    class VipRegistration(Base):
        __tablename__ = "vip_registrations"
        
        id = Column(Integer, primary_key=True, index=True)
        telegram_id = Column(String, nullable=False, index=True)
        telegram_username = Column(String, nullable=True)
        full_name = Column(String, nullable=False)
        email = Column(String, nullable=False)
        phone_number = Column(String, nullable=False)
        brokerage_name = Column(String, nullable=True)
        deposit_amount = Column(String, nullable=True)
        client_id = Column(String, nullable=True)
        ip_address = Column(String, nullable=True)
        user_agent = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'telegram_id': self.telegram_id,
                'telegram_username': self.telegram_username,
                'full_name': self.full_name,
                'email': self.email,
                'phone_number': self.phone_number,
                'brokerage_name': self.brokerage_name,
                'deposit_amount': self.deposit_amount,
                'client_id': self.client_id,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

# Language translations
TRANSLATIONS = {
    'ms': {
        'title': 'Pendaftaran VIP EzyAssist',
        'welcome': 'Selamat datang ke EzyAssist VIP',
        'full_name': 'Nama Penuh',
        'email': 'Alamat Email',
        'phone': 'Nombor Telefon',
        'brokerage': 'Nama Broker',
        'deposit': 'Jumlah Deposit',
        'submit': 'Hantar Pendaftaran',
        'success_title': 'Pendaftaran Berjaya!',
        'success_message': 'Terima kasih! Pendaftaran VIP anda telah berjaya.',
        'error_title': 'Ralat Pendaftaran',
        'required_fields': 'Sila lengkapkan semua medan yang diperlukan',
        'invalid_token': 'Token tidak sah atau telah tamat tempoh'
    }
}

# Utility functions
def generate_registration_token(telegram_id: str, telegram_username: str = "") -> str:
    """Generate secure registration token"""
    try:
        payload = {
            'telegram_id': telegram_id,
            'telegram_username': telegram_username or '',
            'exp': datetime.utcnow() + timedelta(minutes=int(os.getenv('FORM_TIMEOUT_MINUTES', 30))),
            'iat': datetime.utcnow()
        }
        
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            raise ValueError("JWT_SECRET_KEY not configured")
            
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise

def verify_registration_token(token: str) -> tuple[Optional[str], Optional[str]]:
    """Verify and decode registration token"""
    try:
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            logger.error("JWT_SECRET_KEY not configured")
            return None, None
            
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload.get('telegram_id'), payload.get('telegram_username', '')
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None, None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None, None

def generate_form_hash() -> str:
    """Generate form security hash"""
    return hashlib.sha256(f"{time.time()}{secrets.token_hex(16)}".encode()).hexdigest()[:16]

# Database session dependency
def get_db():
    if not SessionLocal:
        return None
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Telegram Bot Class
class EzyAssistBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        self.conversation_engine = ConversationEngine()
        self.supabase_client = SupabaseClient()
        self.engagement_scores = {}
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Save user to database
        await self.supabase_client.upsert_user(telegram_id)
        
        # Initialize engagement score
        self.engagement_scores[telegram_id] = 0
        
        welcome_message = (
            f"Selamat datang ke EzyAssist, {user.first_name}! 🌟\n\n"
            "Saya di sini untuk membantu anda dengan pendidikan forex dan menjawab soalan anda. "
            "Jangan ragu untuk bertanya apa-apa tentang perdagangan forex!\n\n"
            "Untuk pendaftaran VIP, gunakan /register"
        )
        
        await update.message.reply_text(welcome_message)

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /register command"""
        user = update.effective_user
        telegram_id = str(user.id)
        telegram_username = user.username or ""
        
        try:
            # Generate registration token
            token = generate_registration_token(telegram_id, telegram_username)
            
            # Get base URL from environment or construct it
            base_url = os.getenv('BASE_URL', 'https://your-app.repl.co')
            registration_url = f"{base_url}/?token={token}"
            
            register_message = (
                f"🎯 Pendaftaran VIP EzyAssist\n\n"
                f"Klik link di bawah untuk mengisi borang pendaftaran VIP:\n\n"
                f"👉 {registration_url}\n\n"
                f"⏰ Link ini akan tamat tempoh dalam 30 minit.\n"
                f"📝 Sila lengkapkan semua maklumat yang diperlukan."
            )
            
            await update.message.reply_text(register_message)
            logger.info(f"Registration token sent to {telegram_id}")
            
        except Exception as e:
            logger.error(f"Registration command error: {e}")
            await update.message.reply_text(
                "Maaf, ada masalah teknikal. Sila cuba lagi dalam beberapa minit."
            )

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Reset engagement score
        self.engagement_scores[telegram_id] = 0
        
        clear_message = (
            f"✅ Conversation history cleared, {user.first_name}!\n\n"
            "Your engagement score has been reset. Feel free to start fresh with any forex questions!"
        )
        
        await update.message.reply_text(clear_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages"""
        user = update.effective_user
        telegram_id = str(user.id)
        message_text = update.message.text

        # Update engagement score
        if telegram_id not in self.engagement_scores:
            self.engagement_scores[telegram_id] = 0
        self.engagement_scores[telegram_id] += 1

        # Update last seen
        try:
            await self.supabase_client.update_user_last_seen(telegram_id)
        except Exception as e:
            logger.warning(f"Supabase update failed: {e}")

        # Process message through conversation engine
        try:
            response = await self.conversation_engine.process_message(
                message_text, 
                telegram_id, 
                self.engagement_scores[telegram_id]
            )
        except Exception as e:
            logger.error(f"Conversation engine error: {e}")
            response = None

        # Ensure we have a valid response
        if not response or response.strip() == "":
            response = (
                "Maaf awak, saya ada masalah nak jawab soalan ni. "
                "Boleh cuba tanya lagi atau tanya soalan lain?"
            )

        await update.message.reply_text(response)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

    def setup_bot(self):
        """Setup the Telegram bot"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not found")
            return None

        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_error_handler(self.error_handler)

        logger.info("✅ Bot setup completed")
        return self.application

# Initialize bot instance
bot_instance = EzyAssistBot()

# FastAPI Routes
@app.get("/", response_class=HTMLResponse)
async def registration_form(request: Request, token: str = None):
    """Registration form page"""
    if not token:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Missing registration token. Please use the link from the Telegram bot.",
            "translations": TRANSLATIONS['ms']
        })
    
    telegram_id, telegram_username = verify_registration_token(token)
    if not telegram_id:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid or expired registration token",
            "translations": TRANSLATIONS['ms']
        })
    
    # Check if already registered
    if SessionLocal:
        db = get_db()
        if db:
            existing = db.query(VipRegistration).filter_by(telegram_id=telegram_id).first()
            if existing:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": "You have already registered for VIP access",
                    "translations": TRANSLATIONS['ms']
                })
    
    form_hash = generate_form_hash()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "token": token,
        "form_hash": form_hash,
        "translations": TRANSLATIONS['ms']
    })

@app.post("/submit")
async def submit_registration(
    request: Request,
    token: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    brokerage_name: str = Form(...),
    deposit_amount: str = Form(...),
    client_id: str = Form(...),
    deposit_proof_1: UploadFile = File(None),
    deposit_proof_2: UploadFile = File(None),
    deposit_proof_3: UploadFile = File(None)
):
    """Process registration form submission"""
    logger.info("🚨 Registration form submitted")
    
    # Verify token
    telegram_id, telegram_username = verify_registration_token(token)
    if not telegram_id:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Token tidak sah atau telah tamat tempoh",
            "translations": TRANSLATIONS['ms']
        })
    
    # Validate required fields
    if not all([full_name.strip(), email.strip(), phone_number.strip(), brokerage_name.strip(), deposit_amount.strip(), client_id.strip()]):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Sila lengkapkan semua medan yang diperlukan",
            "translations": TRANSLATIONS['ms']
        })
    
    # Save to database if available
    if SessionLocal:
        db = get_db()
        if db:
            try:
                new_registration = VipRegistration(
                    telegram_id=telegram_id,
                    telegram_username=telegram_username or '',
                    full_name=full_name.strip(),
                    email=email.strip(),
                    phone_number=phone_number.strip(),
                    brokerage_name=brokerage_name.strip(),
                    deposit_amount=deposit_amount.strip(),
                    client_id=client_id.strip(),
                    ip_address=request.client.host,
                    user_agent=request.headers.get('User-Agent', '')
                )
                
                db.add(new_registration)
                db.commit()
                logger.info(f"✅ Registration saved for {full_name}")
                
                # Send notification to user via bot
                await send_registration_confirmation(telegram_id, new_registration.to_dict())
                
                # Notify admin
                await send_admin_notification(new_registration.to_dict())
                
            except Exception as e:
                logger.error(f"❌ Database save failed: {e}")
                db.rollback()
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error_message": "Masalah teknikal dengan pangkalan data",
                    "translations": TRANSLATIONS['ms']
                })
    
    # Redirect to success page
    return RedirectResponse(url=f"/success?token={token}", status_code=303)

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, token: str = None):
    """Registration success page"""
    return templates.TemplateResponse("success.html", {
        "request": request,
        "translations": TRANSLATIONS['ms'],
        "token": token
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    bot_ready = False
    if bot_instance and bot_instance.application:
        try:
            # Check if bot application is properly initialized
            bot_ready = hasattr(bot_instance.application, '_initialized') or bot_instance.application.running
        except:
            bot_ready = False
    
    return {
        "status": "ok", 
        "message": "EzyAssist Unified System is running",
        "timestamp": datetime.utcnow().isoformat(),
        "bot_ready": bot_ready,
        "database_ready": bool(SessionLocal and engine)
    }

@app.post("/telegram_webhook")
async def handle_telegram_webhook(request: Request):
    """Handle incoming Telegram updates"""
    try:
        data = await request.json()
        
        if not bot_instance or not bot_instance.application:
            logger.error("Bot not ready")
            return JSONResponse(content={'error': 'Bot not ready'}, status_code=500)
        
        update = Update.de_json(data, bot_instance.application.bot)
        await bot_instance.application.process_update(update)
        
        return JSONResponse(content={'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse(content={'error': 'Server error'}, status_code=500)

# Helper functions for notifications
async def send_registration_confirmation(telegram_id: str, registration_data: dict):
    """Send confirmation message to user"""
    try:
        if bot_instance and bot_instance.application:
            success_message = (
                f"🎉 Pendaftaran VIP berjaya!\n\n"
                f"Terima kasih {registration_data['full_name']}!\n"
                f"Team kami akan hubungi anda dalam 24 jam.\n\n"
                f"📋 Detail pendaftaran:\n"
                f"• Broker: {registration_data.get('brokerage_name', 'N/A')}\n"
                f"• Deposit: ${registration_data.get('deposit_amount', 'N/A')}\n"
                f"• Client ID: {registration_data.get('client_id', 'N/A')}\n\n"
                f"📱 Pastikan phone {registration_data.get('phone_number', 'N/A')} aktif!"
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=success_message
            )
            logger.info(f"✅ Confirmation sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send confirmation: {e}")

async def send_admin_notification(registration_data: dict):
    """Send notification to admin"""
    try:
        if bot_instance and bot_instance.admin_id and bot_instance.application:
            admin_message = (
                f"🔔 NEW VIP REGISTRATION\n\n"
                f"Name: {registration_data.get('full_name', 'N/A')}\n"
                f"Email: {registration_data.get('email', 'N/A')}\n"
                f"Phone: {registration_data.get('phone_number', 'N/A')}\n"
                f"Broker: {registration_data.get('brokerage_name', 'N/A')}\n"
                f"Deposit: ${registration_data.get('deposit_amount', 'N/A')}\n"
                f"Client ID: {registration_data.get('client_id', 'N/A')}\n"
                f"Telegram ID: {registration_data.get('telegram_id', 'N/A')}"
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=bot_instance.admin_id, 
                text=admin_message
            )
            logger.info("✅ Admin notification sent")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

# API Models for external integration
class RegistrationPayload(BaseModel):
    telegram_id: str
    full_name: str
    phone_number: str
    experience_level: str
    client_id: str
    deposit_base64: str = ""

@app.post("/api/register")
async def api_register_user(payload: RegistrationPayload):
    """API endpoint for external registration"""
    try:
        # Process via Supabase if needed
        if bot_instance and bot_instance.supabase_client:
            # Handle image upload if provided
            image_url = ""
            if payload.deposit_base64:
                # Handle image upload logic here
                pass
            
            # Save to Supabase
            data = {
                "telegram_id": payload.telegram_id,
                "full_name": payload.full_name,
                "phone_number": payload.phone_number,
                "experience_level": payload.experience_level,
                "client_id": payload.client_id,
                "deposit_proof": image_url,
            }
            
            # Save to Supabase table
            # supabase.table("registrations").insert(data).execute()
            
            # Send notifications
            await send_registration_confirmation(payload.telegram_id, data)
            await send_admin_notification(data)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"API registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# Bot initialization on startup
async def setup_bot_webhook():
    """Setup bot webhook on startup"""
    try:
        application = bot_instance.setup_bot()
        if application:
            # Initialize the application properly
            await application.initialize()
            webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
            if webhook_url:
                await application.bot.set_webhook(f"{webhook_url}/telegram_webhook")
                logger.info(f"✅ Webhook set to: {webhook_url}/telegram_webhook")
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and bot on startup"""
    # Create database tables
    if Base and engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
    
    # Setup bot webhook
    asyncio.create_task(setup_bot_webhook())

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")