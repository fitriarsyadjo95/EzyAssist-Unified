#!/usr/bin/env python3
"""
EzyAssist Unified System - Combines Telegram Bot and Registration Form
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
import random
import csv
import io
from typing import Optional
import secrets
import hashlib
import time
import uuid
import shutil
from pathlib import Path
from functools import wraps

# FastAPI and web components
from fastapi import FastAPI, Request, Form, HTTPException, status, File, UploadFile, Depends
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Telegram bot components
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Database and external services
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Text, or_, func, text, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import requests
import uvicorn
import enum

# AI and conversation
from conversation_engine import ConversationEngine

# Registration status enum
class RegistrationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
from admin_auth import (
    authenticate_admin, create_admin_session, delete_admin_session,
    get_current_admin, admin_login_required
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.gif'}

async def save_uploaded_file(upload_file: UploadFile) -> Optional[str]:
    """Save uploaded file and return the file path"""
    if not upload_file or not upload_file.filename:
        return None
    
    # Check file extension
    file_extension = Path(upload_file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file extension: {file_extension}")
        return None
    
    # Check file size
    content = await upload_file.read()
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(content)} bytes")
        return None
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}_{int(time.time())}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"File saved: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return None

# Initialize FastAPI app
app = FastAPI(title="EzyAssist Unified System", version="1.0.0")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom exception handler for 401 errors (session expired)
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and "session" in str(exc.detail).lower():
        # Check if this is an AJAX/API request
        if request.headers.get("accept") == "application/json" or "/admin/bot-status" in str(request.url):
            return JSONResponse(
                status_code=401,
                content={"detail": "Session expired", "redirect": "/admin/session-expired"}
            )
        # For regular page requests, redirect to session expired page
        return RedirectResponse(url="/admin/session-expired", status_code=302)
    
    # For all other HTTP exceptions, use default handler
    return await http_exception_handler(request, exc)

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
        deposit_proof_1_path = Column(String, nullable=True)
        deposit_proof_2_path = Column(String, nullable=True)
        deposit_proof_3_path = Column(String, nullable=True)
        status = Column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING, nullable=False)
        status_updated_at = Column(DateTime, nullable=True)
        updated_by_admin = Column(String, nullable=True)
        custom_message = Column(Text, nullable=True)
        on_hold_reason = Column(String, nullable=True)
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
                'deposit_proof_1_path': self.deposit_proof_1_path,
                'deposit_proof_2_path': self.deposit_proof_2_path,
                'deposit_proof_3_path': self.deposit_proof_3_path,
                'status': self.status.value if self.status else 'pending',
                'status_updated_at': self.status_updated_at.isoformat() if self.status_updated_at else None,
                'updated_by_admin': self.updated_by_admin,
                'custom_message': self.custom_message,
                'on_hold_reason': self.on_hold_reason,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    class BotActivity(Base):
        __tablename__ = "bot_activity"
        
        id = Column(Integer, primary_key=True, index=True)
        date = Column(Date, nullable=False, unique=True, index=True)
        total_messages = Column(Integer, default=0)
        unique_users = Column(Integer, default=0)
        new_users = Column(Integer, default=0)
        start_commands = Column(Integer, default=0)
        register_commands = Column(Integer, default=0)
        clear_commands = Column(Integer, default=0)
        errors = Column(Integer, default=0)
        peak_active_users = Column(Integer, default=0)
        avg_response_time = Column(Float, default=0.0)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return {
                'id': self.id,
                'date': self.date.isoformat() if self.date else None,
                'total_messages': self.total_messages,
                'unique_users': self.unique_users,
                'new_users': self.new_users,
                'start_commands': self.start_commands,
                'register_commands': self.register_commands,
                'clear_commands': self.clear_commands,
                'errors': self.errors,
                'peak_active_users': self.peak_active_users,
                'avg_response_time': self.avg_response_time,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
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
        'success_next_steps': 'Langkah Seterusnya',
        'success_step1': 'Pendaftaran anda sedang dalam semakan oleh admin kami',
        'success_step2': 'Anda akan menerima notifikasi dalam Telegram dalam masa 24 jam',
        'success_step3': 'Akses VIP akan diberikan setelah pendaftaran diluluskan',
        'back_to_telegram': 'Kembali ke Telegram',
        'registration_ref': 'Rujukan Pendaftaran',
        'keep_reference': 'Simpan rujukan ini untuk rekod anda',
        'error_title': 'Ralat Pendaftaran',
        'required_fields': 'Sila lengkapkan semua medan yang diperlukan',
        'invalid_token': 'Token tidak sah atau telah tamat tempoh',
        'already_registered': 'Eh, awak dah register untuk VIP access dah! 😊 Jangan risau, kami dah ada rekod pendaftaran awak. Kalau ada masalah atau nak tahu status pendaftaran, boleh terus tanya kat bot Telegram atau hubungi team kami ye!'
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
    return SessionLocal()

# Telegram Bot Class
class EzyAssistBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        self.conversation_engine = ConversationEngine()
        self.engagement_scores = {}
        self.application = None
        
        # Bot activity tracking
        self.start_time = datetime.utcnow()
        self.message_count = 0
        self.user_sessions = {}
        self.command_usage = {
            'start': 0,
            'register': 0,
            'clear': 0
        }
        self.last_activity = None
        self.error_count = 0
        self.daily_users = set()  # Track unique users per day
        self.daily_new_users = set()  # Track new users per day
        self.response_times = []  # Track response times for averaging

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Track activity
        self.command_usage['start'] += 1
        self.last_activity = datetime.utcnow()
        self.user_sessions[telegram_id] = self.last_activity
        
        # Check if new user
        is_new_user = telegram_id not in self.engagement_scores
        
        # Initialize engagement score
        self.engagement_scores[telegram_id] = 0
        
        # Update daily stats in database
        self.update_daily_stats(telegram_id, 'start', is_new_user)
        self.reset_daily_tracking()
        
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
        
        # Track activity
        self.command_usage['register'] += 1
        self.last_activity = datetime.utcnow()
        self.user_sessions[telegram_id] = self.last_activity
        
        # Update daily stats in database
        self.update_daily_stats(telegram_id, 'register')
        self.reset_daily_tracking()
        
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
        
        # Track activity
        self.command_usage['clear'] += 1
        self.last_activity = datetime.utcnow()
        self.user_sessions[telegram_id] = self.last_activity
        
        # Update daily stats in database
        self.update_daily_stats(telegram_id, 'clear')
        self.reset_daily_tracking()
        
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

        # Track activity
        self.message_count += 1
        self.last_activity = datetime.utcnow()
        self.user_sessions[telegram_id] = self.last_activity

        # Check if new user
        is_new_user = telegram_id not in self.engagement_scores

        # Update engagement score
        if telegram_id not in self.engagement_scores:
            self.engagement_scores[telegram_id] = 0
        self.engagement_scores[telegram_id] += 1

        # Update daily stats in database
        self.update_daily_stats(telegram_id, 'message', is_new_user)
        self.reset_daily_tracking()

        # Update last seen (removed Supabase dependency)

        # Process message through conversation engine
        try:
            response = await self.conversation_engine.process_message(
                message_text, 
                telegram_id, 
                self.engagement_scores[telegram_id],
                user.username or ""
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
        self.error_count += 1
        self.update_daily_stats(errors=1)
        logger.error(f"Update {update} caused error {context.error}")

    def get_bot_statistics(self):
        """Get comprehensive bot statistics"""
        current_time = datetime.utcnow()
        
        # Calculate uptime
        uptime_delta = current_time - self.start_time
        uptime_hours = uptime_delta.total_seconds() / 3600
        
        # Get active users (users who interacted in last 30 minutes)
        active_threshold = current_time - timedelta(minutes=30)
        active_users = sum(1 for last_seen in self.user_sessions.values() 
                          if last_seen and last_seen > active_threshold)
        
        # Get messages today
        if self.last_activity:
            today = current_time.date()
            if self.last_activity.date() == today:
                messages_today = self.message_count
            else:
                messages_today = 0
        else:
            messages_today = 0
        
        # Calculate response rate (messages - errors)
        total_interactions = sum(self.command_usage.values()) + self.message_count
        success_rate = ((total_interactions - self.error_count) / max(total_interactions, 1)) * 100
        
        return {
            'bot_status': 'online' if self.application and hasattr(self.application, 'running') else 'offline',
            'uptime_hours': round(uptime_hours, 1),
            'total_users': len(self.user_sessions),
            'active_users': active_users,
            'total_messages': self.message_count,
            'messages_today': messages_today,
            'command_usage': self.command_usage.copy(),
            'success_rate': round(success_rate, 1),
            'error_count': self.error_count,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'engagement_scores': dict(list(sorted(self.engagement_scores.items(), 
                                                key=lambda x: x[1], reverse=True))[:5])
        }

    def get_bot_health(self):
        """Get bot health status"""
        try:
            is_running = bool(self.application and self.token)
            webhook_status = 'connected' if is_running else 'disconnected'
            
            current_time = datetime.utcnow()
            uptime_delta = current_time - self.start_time
            
            return {
                'status': 'healthy' if is_running else 'unhealthy',
                'uptime': str(uptime_delta).split('.')[0],  # Remove microseconds
                'webhook_status': webhook_status,
                'last_activity': self.last_activity.strftime('%Y-%m-%d %H:%M:%S UTC') if self.last_activity else 'Never',
                'error_rate': round((self.error_count / max(self.message_count, 1)) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error getting bot health: {e}")
            return {
                'status': 'error',
                'uptime': '0:00:00',
                'webhook_status': 'error',
                'last_activity': 'Error',
                'error_rate': 100.0
            }

    def update_daily_stats(self, telegram_id: str, command_type: str = 'message', is_new_user: bool = False):
        """Update daily statistics in database"""
        try:
            if not SessionLocal:
                return
                
            db = SessionLocal()
            today = datetime.utcnow().date()
            
            # Get or create today's record
            daily_stats = db.query(BotActivity).filter_by(date=today).first()
            if not daily_stats:
                daily_stats = BotActivity(date=today)
                db.add(daily_stats)
            
            # Update statistics
            if command_type == 'message':
                daily_stats.total_messages += 1
            elif command_type == 'start':
                daily_stats.start_commands += 1
            elif command_type == 'register':
                daily_stats.register_commands += 1
            elif command_type == 'clear':
                daily_stats.clear_commands += 1
            elif command_type == 'error':
                daily_stats.errors += 1
            
            # Track unique users
            self.daily_users.add(telegram_id)
            daily_stats.unique_users = len(self.daily_users)
            
            # Track new users
            if is_new_user:
                self.daily_new_users.add(telegram_id)
                daily_stats.new_users = len(self.daily_new_users)
            
            # Update peak active users
            current_active = len([ts for ts in self.user_sessions.values() 
                                if ts and ts > datetime.utcnow() - timedelta(minutes=30)])
            if current_active > daily_stats.peak_active_users:
                daily_stats.peak_active_users = current_active
            
            # Update average response time
            if self.response_times:
                daily_stats.avg_response_time = sum(self.response_times) / len(self.response_times)
            
            daily_stats.updated_at = datetime.utcnow()
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
            if 'db' in locals():
                db.close()

    def get_historical_stats(self, days: int = 30):
        """Get historical bot activity stats"""
        try:
            if not SessionLocal:
                return []
                
            db = SessionLocal()
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days-1)
            
            stats = db.query(BotActivity).filter(
                BotActivity.date >= start_date,
                BotActivity.date <= end_date
            ).order_by(BotActivity.date.desc()).all()
            
            db.close()
            return [stat.to_dict() for stat in stats]
            
        except Exception as e:
            logger.error(f"Error getting historical stats: {e}")
            if 'db' in locals():
                db.close()
            return []

    def reset_daily_tracking(self):
        """Reset daily tracking sets (call at midnight)"""
        current_date = datetime.utcnow().date()
        if hasattr(self, '_last_reset_date') and self._last_reset_date == current_date:
            return
            
        self.daily_users = set()
        self.daily_new_users = set()
        self.response_times = []
        self._last_reset_date = current_date

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
                    "error_message": TRANSLATIONS['ms']['already_registered'],
                    "translations": TRANSLATIONS['ms'],
                    "lang": "ms"
                })
    
    form_hash = generate_form_hash()
    return templates.TemplateResponse("simple_form.html", {
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
    
    # Debug: Log received form data
    logger.info(f"Received token: {token if token else 'MISSING'}")
    logger.info(f"Received full_name: {full_name if full_name else 'MISSING'}")
    logger.info(f"Received email: {email if email else 'MISSING'}")
    logger.info(f"Received phone_number: {phone_number if phone_number else 'MISSING'}")
    logger.info(f"Received brokerage_name: {brokerage_name if brokerage_name else 'MISSING'}")
    logger.info(f"Received deposit_amount: {deposit_amount if deposit_amount else 'MISSING'}")
    logger.info(f"Received client_id: {client_id if client_id else 'MISSING'}")
    
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
    
    # Process file uploads
    deposit_proof_1_path = await save_uploaded_file(deposit_proof_1)
    deposit_proof_2_path = await save_uploaded_file(deposit_proof_2)
    deposit_proof_3_path = await save_uploaded_file(deposit_proof_3)
    
    logger.info(f"Files saved: {deposit_proof_1_path}, {deposit_proof_2_path}, {deposit_proof_3_path}")
    
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
                    deposit_proof_1_path=deposit_proof_1_path,
                    deposit_proof_2_path=deposit_proof_2_path,
                    deposit_proof_3_path=deposit_proof_3_path,
                    ip_address=request.client.host,
                    user_agent=request.headers.get('User-Agent', '')
                )
                
                db.add(new_registration)
                db.commit()
                logger.info(f"✅ Registration saved for {full_name}")
                
                # Send pending notification to user via bot
                await send_registration_pending(telegram_id, new_registration.to_dict())
                
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
    telegram_id = None
    telegram_username = None
    
    if token:
        telegram_id, telegram_username = verify_registration_token(token)
    
    return templates.TemplateResponse("success.html", {
        "request": request,
        "translations": TRANSLATIONS['ms'],
        "token": token,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "lang": "ms"
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

@app.get("/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    """Serve uploaded files (with basic security check)"""
    file_path = UPLOAD_DIR / filename
    
    # Security check: ensure file exists and is within upload directory
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Additional security: ensure file is within uploads directory
    try:
        file_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine media type based on file extension
    media_type = "application/octet-stream"
    suffix = file_path.suffix.lower()
    if suffix in ['.jpg', '.jpeg']:
        media_type = "image/jpeg"
    elif suffix == '.png':
        media_type = "image/png"
    elif suffix == '.gif':
        media_type = "image/gif"
    elif suffix == '.pdf':
        media_type = "application/pdf"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

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
async def send_registration_pending(telegram_id: str, registration_data: dict):
    """Send pending review message to user"""
    try:
        if bot_instance and bot_instance.application:
            pending_message = (
                f"📝 Pendaftaran VIP Diterima!\n\n"
                f"Terima kasih {registration_data['full_name']}!\n\n"
                f"🔍 Pendaftaran anda sedang dalam semakan oleh team kami.\n"
                f"📋 Kami akan semak semua maklumat dan dokumen yang dihantar.\n\n"
                f"⏰ Status akan dikemaskini dalam masa 24-48 jam.\n"
                f"📱 Pastikan phone {registration_data.get('phone_number', 'N/A')} aktif untuk makluman!\n\n"
                f"🙏 Terima kasih atas kesabaran anda."
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=pending_message
            )
            logger.info(f"✅ Pending notification sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send pending notification: {e}")

async def send_vip_access_granted(telegram_id: str, registration_data: dict):
    """Send VIP access granted message to user"""
    try:
        if bot_instance and bot_instance.application:
            vip_message = (
                f"🎉 SELAMAT! VIP Access Diluluskan!\n\n"
                f"Hai {registration_data['full_name']},\n\n"
                f"✅ Pendaftaran VIP anda telah DILULUSKAN!\n"
                f"🔥 Anda kini boleh akses semua content VIP kami.\n\n"
                f"🔗 VIP Link: https://mock-vip-link.com/access\n"
                f"📱 Telegram VIP Group: https://t.me/ezyassist_vip\n\n"
                f"💎 Selamat menikmati perkhidmatan VIP EzyAssist!\n"
                f"📞 Jika ada soalan, hubungi team support kami."
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=vip_message
            )
            logger.info(f"✅ VIP access granted message sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send VIP access message: {e}")

async def send_registration_rejected(telegram_id: str, registration_data: dict):
    """Send registration rejected message to user"""
    try:
        if bot_instance and bot_instance.application:
            rejected_message = (
                f"⚠️ Pendaftaran VIP - Tindakan Diperlukan\n\n"
                f"Hai {registration_data['full_name']},\n\n"
                f"🔍 Setelah semakan, kami dapati ada beberapa isu dengan pendaftaran anda yang perlu diselesaikan.\n\n"
                f"📞 Team kami akan hubungi anda dalam masa 24 jam untuk:\n"
                f"• Menjelaskan isu yang ditemui\n"
                f"• Membantu menyelesaikan masalah\n"
                f"• Meneruskan proses pendaftaran\n\n"
                f"📱 Pastikan phone {registration_data.get('phone_number', 'N/A')} aktif!\n\n"
                f"🙏 Terima kasih atas kesabaran anda."
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=rejected_message
            )
            logger.info(f"✅ Registration rejected message sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send rejection message: {e}")

async def send_registration_on_hold(telegram_id: str, registration_data: dict, custom_message: str, hold_reason: str = None):
    """Send registration on hold message with custom admin message"""
    try:
        if bot_instance and bot_instance.application:
            on_hold_message = (
                f"⏸️ Pendaftaran VIP - Tindakan Diperlukan\n\n"
                f"Hai {registration_data['full_name']},\n\n"
                f"Pendaftaran VIP anda sedang dalam semakan. Team kami memerlukan maklumat tambahan:\n\n"
                f"📝 **Mesej daripada Admin:**\n"
                f"{custom_message}\n\n"
            )
            
            if hold_reason:
                on_hold_message += f"📋 **Kategori:** {hold_reason}\n\n"
            
            on_hold_message += (
                f"📞 Sila reply message ini atau hubungi kami dalam masa 7 hari untuk meneruskan pendaftaran.\n\n"
                f"📱 Pastikan phone {registration_data.get('phone_number', 'N/A')} aktif untuk makluman!\n\n"
                f"🙏 Terima kasih atas kerjasama anda."
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=on_hold_message
            )
            logger.info(f"✅ Registration on hold message sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send on hold message: {e}")

async def send_admin_notification(registration_data: dict):
    """Send notification to admin"""
    try:
        if bot_instance and bot_instance.admin_id and bot_instance.application:
            admin_message = (
                f"🔔 NEW VIP REGISTRATION - REVIEW REQUIRED\n\n"
                f"📋 Registration #{registration_data.get('id', 'N/A')}\n"
                f"👤 Name: {registration_data.get('full_name', 'N/A')}\n"
                f"📧 Email: {registration_data.get('email', 'N/A')}\n"
                f"📱 Phone: {registration_data.get('phone_number', 'N/A')}\n"
                f"🏢 Broker: {registration_data.get('brokerage_name', 'N/A')}\n"
                f"💰 Deposit: ${registration_data.get('deposit_amount', 'N/A')}\n"
                f"🆔 Client ID: {registration_data.get('client_id', 'N/A')}\n"
                f"📲 Telegram: {registration_data.get('telegram_id', 'N/A')}\n\n"
                f"⚠️ Status: PENDING REVIEW\n"
                f"🔗 Admin Panel: /admin/registrations/{registration_data.get('id', '')}"
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
        # Process registration data
        data = {
            "telegram_id": payload.telegram_id,
            "full_name": payload.full_name,
            "phone_number": payload.phone_number,
            "experience_level": payload.experience_level,
            "client_id": payload.client_id,
        }
        
        # Send notifications
        await send_registration_confirmation(payload.telegram_id, data)
        await send_admin_notification(data)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"API registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# =============================================================================
# ADMIN DASHBOARD ROUTES
# =============================================================================

@app.get("/admin/session-expired", response_class=HTMLResponse)
async def admin_session_expired(request: Request):
    """Session expired page"""
    return templates.TemplateResponse("admin/session_expired.html", {
        "request": request
    })

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {
        "request": request
    })

@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Process admin login"""
    if authenticate_admin(username, password):
        session_token = create_admin_session(username)
        response = RedirectResponse(url="/admin/", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            max_age=3600,   # 1 hour
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        return response
    else:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Admin logout"""
    admin_session = request.cookies.get("admin_session")
    if admin_session:
        delete_admin_session(admin_session)
    
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(key="admin_session")
    return response

@app.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin = Depends(get_current_admin)):
    """Admin dashboard overview"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    # Get statistics
    stats = {}
    if SessionLocal:
        db = get_db()
        if db:
            try:
                # Total registrations
                total_registrations = db.query(VipRegistration).count()
                
                # Recent registrations (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_registrations = db.query(VipRegistration).filter(
                    VipRegistration.created_at >= week_ago
                ).count()
                
                # Status statistics
                pending_count = db.query(VipRegistration).filter(
                    VipRegistration.status == RegistrationStatus.PENDING
                ).count()
                verified_count = db.query(VipRegistration).filter(
                    VipRegistration.status == RegistrationStatus.VERIFIED
                ).count()
                rejected_count = db.query(VipRegistration).filter(
                    VipRegistration.status == RegistrationStatus.REJECTED
                ).count()
                on_hold_count = db.query(VipRegistration).filter(
                    VipRegistration.status == RegistrationStatus.ON_HOLD
                ).count()
                
                # Registrations by broker
                broker_stats = db.query(
                    VipRegistration.brokerage_name,
                    func.count(VipRegistration.id).label('count')
                ).group_by(VipRegistration.brokerage_name).all()
                
                stats = {
                    "total_registrations": total_registrations,
                    "recent_registrations": recent_registrations,
                    "pending_count": pending_count,
                    "verified_count": verified_count,
                    "rejected_count": rejected_count,
                    "on_hold_count": on_hold_count,
                    "broker_stats": broker_stats
                }
            except Exception as e:
                logger.error(f"Error getting admin stats: {e}")
                stats = {"error": "Could not load statistics"}
            finally:
                db.close()
    
    # Get bot statistics
    bot_stats = {}
    bot_health = {}
    try:
        if bot_instance:
            bot_stats = bot_instance.get_bot_statistics()
            bot_health = bot_instance.get_bot_health()
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        bot_stats = {"error": "Could not load bot statistics"}
        bot_health = {"status": "error", "uptime": "Unknown"}

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "stats": stats,
        "bot_stats": bot_stats,
        "bot_health": bot_health
    })

@app.get("/admin/bot-status")
async def get_bot_status(admin = Depends(get_current_admin)):
    """API endpoint for real-time bot status"""
    try:
        if bot_instance:
            bot_stats = bot_instance.get_bot_statistics()
            bot_health = bot_instance.get_bot_health()
            return {
                "success": True,
                "bot_stats": bot_stats,
                "bot_health": bot_health
            }
        else:
            return {
                "success": False,
                "error": "Bot instance not available"
            }
    except Exception as e:
        logger.error(f"Error in bot status endpoint: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/admin/bot-activity", response_class=HTMLResponse)
async def admin_bot_activity(request: Request, admin = Depends(get_current_admin)):
    """Admin bot activity page with historical data"""
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    historical_data = []
    current_stats = {}
    
    if SessionLocal:
        db = get_db()
        if db:
            try:
                # Get historical activity data (last 30 days)
                thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
                historical_data = db.query(BotActivity).filter(
                    BotActivity.date >= thirty_days_ago
                ).order_by(BotActivity.date.desc()).all()
                
                # Get current bot statistics
                if bot_instance:
                    current_stats = bot_instance.get_bot_statistics()
                    
            except Exception as e:
                logger.error(f"Error getting bot activity data: {e}")
            finally:
                db.close()
    
    return templates.TemplateResponse("admin/bot_activity.html", {
        "request": request,
        "admin": admin,
        "historical_data": historical_data,
        "current_stats": current_stats
    })

@app.get("/admin/registrations", response_class=HTMLResponse)
async def admin_registrations_list(
    request: Request, 
    page: int = 1, 
    search: str = "",
    status: str = "",
    admin = Depends(get_current_admin)
):
    """Admin registrations list with pagination and search"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    registrations = []
    total_pages = 1
    total_count = 0
    
    if SessionLocal:
        db = get_db()
        if db:
            try:
                # Base query
                query = db.query(VipRegistration)
                
                # Add search filter
                if search:
                    search_filter = f"%{search}%"
                    query = query.filter(
                        or_(
                            VipRegistration.full_name.ilike(search_filter),
                            VipRegistration.email.ilike(search_filter),
                            VipRegistration.brokerage_name.ilike(search_filter),
                            VipRegistration.telegram_username.ilike(search_filter)
                        )
                    )
                
                # Add status filter
                if status:
                    if status == "pending":
                        query = query.filter(VipRegistration.status == RegistrationStatus.PENDING)
                    elif status == "verified":
                        query = query.filter(VipRegistration.status == RegistrationStatus.VERIFIED)
                    elif status == "rejected":
                        query = query.filter(VipRegistration.status == RegistrationStatus.REJECTED)
                    elif status == "on_hold":
                        query = query.filter(VipRegistration.status == RegistrationStatus.ON_HOLD)
                
                # Get total count
                total_count = query.count()
                
                # Pagination
                per_page = 20
                total_pages = (total_count + per_page - 1) // per_page
                offset = (page - 1) * per_page
                
                # Get registrations
                registrations = query.order_by(
                    VipRegistration.created_at.desc()
                ).offset(offset).limit(per_page).all()
                
            except Exception as e:
                logger.error(f"Error getting registrations: {e}")
            finally:
                db.close()
    
    return templates.TemplateResponse("admin/registrations.html", {
        "request": request,
        "admin": admin,
        "registrations": registrations,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "search": search,
        "status": status
    })

@app.get("/admin/registrations/export")
async def export_registrations(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    status: str = "",
    format: str = "csv",
    admin = Depends(get_current_admin)
):
    """Export registrations to CSV with optional date and status filtering"""
    
    # Check if this is a direct browser request (not AJAX) and redirect to registrations page
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and "application/json" not in accept_header:
        # This is a direct browser request, redirect to registrations page with message
        return RedirectResponse(url="/admin/registrations?message=use_export_button", status_code=302)
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Build query with filters
        query = db.query(VipRegistration)
        
        # Date filtering
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(VipRegistration.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include full end day
                query = query.filter(VipRegistration.created_at < end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Status filtering
        if status:
            if status == "pending":
                query = query.filter(VipRegistration.status == RegistrationStatus.PENDING)
            elif status == "verified":
                query = query.filter(VipRegistration.status == RegistrationStatus.VERIFIED)
            elif status == "rejected":
                query = query.filter(VipRegistration.status == RegistrationStatus.REJECTED)
            elif status == "on_hold":
                query = query.filter(VipRegistration.status == RegistrationStatus.ON_HOLD)
        
        # Get filtered registrations
        registrations = query.order_by(VipRegistration.created_at.desc()).all()
        
        if format.lower() == "csv":
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Registration Date', 'Full Name', 'Email', 'Phone Number',
                'Telegram ID', 'Telegram Username', 'Client ID', 'Brokerage Name',
                'Deposit Amount', 'Status', 'IP Address', 'Status Updated At',
                'Updated By Admin', 'Files Count'
            ])
            
            # Write data rows
            for reg in registrations:
                # Count uploaded files
                file_count = sum(1 for path in [
                    reg.deposit_proof_1_path,
                    reg.deposit_proof_2_path, 
                    reg.deposit_proof_3_path
                ] if path)
                
                writer.writerow([
                    reg.id,
                    reg.created_at.strftime('%Y-%m-%d %H:%M:%S') if reg.created_at else '',
                    reg.full_name,
                    reg.email,
                    reg.phone_number,
                    reg.telegram_id,
                    reg.telegram_username or '',
                    reg.client_id,
                    reg.brokerage_name,
                    reg.deposit_amount,
                    reg.status.value if reg.status else '',
                    reg.ip_address or '',
                    reg.status_updated_at.strftime('%Y-%m-%d %H:%M:%S') if reg.status_updated_at else '',
                    reg.updated_by_admin or '',
                    file_count
                ])
            
            # Generate filename with filters
            filename_parts = ["ezyassist_registrations"]
            if start_date and end_date:
                filename_parts.append(f"{start_date}_to_{end_date}")
            elif start_date:
                filename_parts.append(f"from_{start_date}")
            elif end_date:
                filename_parts.append(f"until_{end_date}")
            
            if status:
                filename_parts.append(f"status_{status}")
            
            filename_parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
            filename = "_".join(filename_parts) + ".csv"
            
            # Log export activity
            logger.info(f"📊 Registration export by {admin.get('username')} - {len(registrations)} records, filters: start={start_date}, end={end_date}, status={status}")
            
            # Return CSV file
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Only 'csv' is supported.")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting registrations: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    finally:
        db.close()

@app.get("/admin/registrations/{registration_id}", response_class=HTMLResponse)
async def admin_registration_detail(
    request: Request, 
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """Admin registration detail page"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    registration = None
    if SessionLocal:
        db = get_db()
        if db:
            try:
                registration = db.query(VipRegistration).filter(
                    VipRegistration.id == registration_id
                ).first()
            except Exception as e:
                logger.error(f"Error getting registration {registration_id}: {e}")
            finally:
                db.close()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return templates.TemplateResponse("admin/registration_detail.html", {
        "request": request,
        "admin": admin,
        "registration": registration
    })

@app.post("/admin/registrations/{registration_id}/verify")
async def verify_registration(
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """Verify a registration and grant VIP access"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Get registration
        registration = db.query(VipRegistration).filter(
            VipRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Update status
        registration.status = RegistrationStatus.VERIFIED
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        
        db.commit()
        
        # Send VIP access message to user
        await send_vip_access_granted(registration.telegram_id, registration.to_dict())
        
        logger.info(f"✅ Registration {registration_id} verified by {admin.get('username')}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Registration verified and VIP access granted"
        })
        
    except Exception as e:
        logger.error(f"Error verifying registration {registration_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify registration")
    finally:
        db.close()

@app.post("/admin/registrations/{registration_id}/reject")
async def reject_registration(
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """Reject a registration and send follow-up message"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Get registration
        registration = db.query(VipRegistration).filter(
            VipRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Update status
        registration.status = RegistrationStatus.REJECTED
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        
        db.commit()
        
        # Send rejection message to user
        await send_registration_rejected(registration.telegram_id, registration.to_dict())
        
        logger.info(f"✅ Registration {registration_id} rejected by {admin.get('username')}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Registration rejected and user notified"
        })
        
    except Exception as e:
        logger.error(f"Error rejecting registration {registration_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reject registration")
    finally:
        db.close()

# Hold registration request model
class HoldRegistrationRequest(BaseModel):
    custom_message: str
    hold_reason: Optional[str] = None

@app.post("/admin/registrations/{registration_id}/hold")
async def hold_registration(
    registration_id: int,
    request: HoldRegistrationRequest,
    admin = Depends(get_current_admin)
):
    """Put a registration on hold with custom message"""
    logger.info(f"Hold registration request received for ID: {registration_id}")
    
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Validate custom message
    if not request.custom_message or not request.custom_message.strip():
        raise HTTPException(status_code=400, detail="Custom message is required")
    
    if len(request.custom_message.strip()) > 500:
        raise HTTPException(status_code=400, detail="Custom message must not exceed 500 characters")
    
    try:
        # Get registration
        registration = db.query(VipRegistration).filter(
            VipRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Update status
        registration.status = RegistrationStatus.ON_HOLD
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        registration.custom_message = request.custom_message.strip()
        registration.on_hold_reason = request.hold_reason.strip() if request.hold_reason else None
        
        db.commit()
        
        # Send on hold message to user
        await send_registration_on_hold(
            registration.telegram_id, 
            registration.to_dict(), 
            request.custom_message.strip(),
            request.hold_reason.strip() if request.hold_reason else None
        )
        
        logger.info(f"✅ Registration {registration_id} put on hold by {admin.get('username')}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Registration put on hold and user notified with custom message"
        })
        
    except Exception as e:
        logger.error(f"Error holding registration {registration_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to put registration on hold")
    finally:
        db.close()

@app.post("/admin/registrations/delete-all")
async def delete_all_registrations(admin = Depends(get_current_admin)):
    """Delete all registration records (admin only)"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Get count before deletion
        count_before = db.query(VipRegistration).count()
        
        # Delete all registrations
        db.query(VipRegistration).delete()
        db.commit()
        
        logger.info(f"✅ All registrations deleted by {admin.get('username')} - {count_before} records removed")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"All {count_before} registration records have been deleted",
            "deleted_count": count_before
        })
        
    except Exception as e:
        logger.error(f"Error deleting all registrations: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete registrations")
    finally:
        db.close()

@app.post("/admin/registrations/create-test-data")
async def create_test_registrations(admin = Depends(get_current_admin)):
    """Create test registration data - 10 verified, 5 rejected (admin only)"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Test registration data
    test_users = [
        # 10 Verified Users
        {
            "telegram_id": "1234567890", "telegram_username": "ahmad_trader", 
            "full_name": "Ahmad Bin Abdullah", "email": "ahmad.abdullah@gmail.com",
            "phone_number": "+60123456789", "client_id": "EXNESS_MY_001",
            "brokerage_name": "Exness", "deposit_amount": 500, "status": "verified", "days_ago": 5
        },
        {
            "telegram_id": "2345678901", "telegram_username": "siti_forex",
            "full_name": "Siti Nurhaliza Binti Rashid", "email": "siti.nurhaliza@yahoo.com", 
            "phone_number": "+60198765432", "client_id": "XM_MY_002",
            "brokerage_name": "XM Global", "deposit_amount": 750, "status": "verified", "days_ago": 8
        },
        {
            "telegram_id": "3456789012", "telegram_username": "mohd_profit",
            "full_name": "Mohammad Hafiz Bin Omar", "email": "hafiz.omar@hotmail.com",
            "phone_number": "+60187654321", "client_id": "FXCM_MY_003", 
            "brokerage_name": "FXCM", "deposit_amount": 300, "status": "verified", "days_ago": 12
        },
        {
            "telegram_id": "4567890123", "telegram_username": "farah_trading",
            "full_name": "Farah Aisyah Binti Zainal", "email": "farah.aisyah@gmail.com",
            "phone_number": "+60176543210", "client_id": "IC_MARKETS_004",
            "brokerage_name": "IC Markets", "deposit_amount": 1000, "status": "verified", "days_ago": 3
        },
        {
            "telegram_id": "5678901234", "telegram_username": "azman_fx",
            "full_name": "Azman Bin Yusof", "email": "azman.yusof@gmail.com",
            "phone_number": "+60165432109", "client_id": "PEPPERSTONE_005",
            "brokerage_name": "Pepperstone", "deposit_amount": 600, "status": "verified", "days_ago": 15
        },
        {
            "telegram_id": "6789012345", "telegram_username": "lisa_invest", 
            "full_name": "Lisa Tan Wei Ling", "email": "lisa.tan@outlook.com",
            "phone_number": "+60154321098", "client_id": "AVATRADE_006",
            "brokerage_name": "AvaTrade", "deposit_amount": 450, "status": "verified", "days_ago": 7
        },
        {
            "telegram_id": "7890123456", "telegram_username": "rizal_capital",
            "full_name": "Rizal Bin Hashim", "email": "rizal.hashim@gmail.com", 
            "phone_number": "+60143210987", "client_id": "FXTM_007",
            "brokerage_name": "FXTM", "deposit_amount": 800, "status": "verified", "days_ago": 20
        },
        {
            "telegram_id": "8901234567", "telegram_username": "nina_trader",
            "full_name": "Nina Safiya Binti Ahmad", "email": "nina.safiya@yahoo.com",
            "phone_number": "+60132109876", "client_id": "HOTFOREX_008",
            "brokerage_name": "HotForex", "deposit_amount": 550, "status": "verified", "days_ago": 1
        },
        {
            "telegram_id": "9012345678", "telegram_username": "daniel_pro",
            "full_name": "Daniel Lim Chee Wei", "email": "daniel.lim@gmail.com",
            "phone_number": "+60121098765", "client_id": "PLUS500_009", 
            "brokerage_name": "Plus500", "deposit_amount": 900, "status": "verified", "days_ago": 10
        },
        {
            "telegram_id": "0123456789", "telegram_username": "sarah_wealth",
            "full_name": "Sarah Binti Ibrahim", "email": "sarah.ibrahim@hotmail.com",
            "phone_number": "+60110987654", "client_id": "TICKMILL_010",
            "brokerage_name": "Tickmill", "deposit_amount": 650, "status": "verified", "days_ago": 6
        },
        
        # 5 Rejected Users
        {
            "telegram_id": "1111111111", "telegram_username": "rejected_user1",
            "full_name": "Ali Bin Hassan", "email": "ali.hassan@gmail.com",
            "phone_number": "+60191111111", "client_id": "INVALID_001",
            "brokerage_name": "Unknown Broker", "deposit_amount": 100, "status": "rejected", "days_ago": 2
        },
        {
            "telegram_id": "2222222222", "telegram_username": "rejected_user2",
            "full_name": "Mira Binti Kamal", "email": "fake.email@invalid.com",
            "phone_number": "+60192222222", "client_id": "FAKE_002", 
            "brokerage_name": "Scam Broker", "deposit_amount": 200, "status": "rejected", "days_ago": 4
        },
        {
            "telegram_id": "3333333333", "telegram_username": "rejected_user3",
            "full_name": "Kumar Ramasamy", "email": "kumar.test@test.com",
            "phone_number": "+60193333333", "client_id": "TEST_003",
            "brokerage_name": "Test Broker", "deposit_amount": 150, "status": "rejected", "days_ago": 9
        },
        {
            "telegram_id": "4444444444", "telegram_username": "rejected_user4", 
            "full_name": "Wei Ming Tan", "email": "weiming@dummy.com",
            "phone_number": "+60194444444", "client_id": "DUMMY_004",
            "brokerage_name": "Fake Markets", "deposit_amount": 75, "status": "rejected", "days_ago": 11
        },
        {
            "telegram_id": "5555555555", "telegram_username": "rejected_user5",
            "full_name": "Raj Singh", "email": "raj.singh@invalid.org",
            "phone_number": "+60195555555", "client_id": "INVALID_005",
            "brokerage_name": "Non-existent Broker", "deposit_amount": 250, "status": "rejected", "days_ago": 14
        }
    ]
    
    try:
        created_count = 0
        skipped_count = 0
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(VipRegistration).filter_by(
                telegram_id=user_data["telegram_id"]
            ).first()
            
            if existing_user:
                skipped_count += 1
                continue
            
            # Calculate registration date
            registration_date = datetime.utcnow() - timedelta(days=user_data["days_ago"])
            
            # Create registration record
            registration = VipRegistration(
                telegram_id=user_data["telegram_id"],
                telegram_username=user_data["telegram_username"], 
                full_name=user_data["full_name"],
                email=user_data["email"],
                phone_number=user_data["phone_number"],
                client_id=user_data["client_id"],
                brokerage_name=user_data["brokerage_name"],
                deposit_amount=user_data["deposit_amount"],
                status=RegistrationStatus.VERIFIED if user_data["status"] == "verified" else RegistrationStatus.REJECTED,
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Test Data Generator)",
                created_at=registration_date,
                status_updated_at=registration_date + timedelta(hours=random.randint(1, 48)),
                updated_by_admin="test_admin"
            )
            
            db.add(registration)
            created_count += 1
        
        db.commit()
        
        verified_count = len([u for u in test_users if u["status"] == "verified"])
        rejected_count = len([u for u in test_users if u["status"] == "rejected"])
        
        logger.info(f"✅ Test data created by {admin.get('username')} - {created_count} records created")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Test data created successfully",
            "created": created_count,
            "skipped": skipped_count,
            "verified": verified_count,
            "rejected": rejected_count,
            "total": len(test_users)
        })
        
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test data: {str(e)}")
    finally:
        db.close()


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

async def migrate_database():
    """Migrate database schema for new file upload columns"""
    if not engine:
        return
    
    try:
        with engine.connect() as conn:
            # Check if new columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'vip_registrations' 
                AND column_name IN ('deposit_proof_1_path', 'deposit_proof_2_path', 'deposit_proof_3_path')
            """))
            existing_columns = [row[0] for row in result]
            
            # Add missing columns
            columns_to_add = [
                'deposit_proof_1_path',
                'deposit_proof_2_path', 
                'deposit_proof_3_path'
            ]
            
            for column in columns_to_add:
                if column not in existing_columns:
                    conn.execute(text(f"""
                        ALTER TABLE vip_registrations 
                        ADD COLUMN {column} VARCHAR
                    """))
                    conn.commit()
                    logger.info(f"✅ Added column: {column}")
            
            # Check for status-related columns
            status_result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'vip_registrations' 
                AND column_name IN ('status', 'status_updated_at', 'updated_by_admin')
            """))
            existing_status_columns = [row[0] for row in status_result]
            
            # Add status column if missing
            if 'status' not in existing_status_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN status VARCHAR DEFAULT 'PENDING'
                """))
                conn.commit()
                logger.info("✅ Added column: status")
                
                # Set existing registrations to pending (using enum values)
                conn.execute(text("""
                    UPDATE vip_registrations 
                    SET status = 'PENDING' 
                    WHERE status IS NULL OR status = 'pending'
                """))
                conn.commit()
                logger.info("✅ Set existing registrations to PENDING status")
            
            # Add status_updated_at column if missing
            if 'status_updated_at' not in existing_status_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN status_updated_at TIMESTAMP
                """))
                conn.commit()
                logger.info("✅ Added column: status_updated_at")
            
            # Add updated_by_admin column if missing
            if 'updated_by_admin' not in existing_status_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN updated_by_admin VARCHAR
                """))
                conn.commit()
                logger.info("✅ Added column: updated_by_admin")
            
            # Check for new ON_HOLD columns
            on_hold_result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'vip_registrations' 
                AND column_name IN ('custom_message', 'on_hold_reason')
            """))
            existing_on_hold_columns = [row[0] for row in on_hold_result]
            
            # Add custom_message column if missing
            if 'custom_message' not in existing_on_hold_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN custom_message TEXT
                """))
                conn.commit()
                logger.info("✅ Added column: custom_message")
            
            # Add on_hold_reason column if missing
            if 'on_hold_reason' not in existing_on_hold_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN on_hold_reason VARCHAR
                """))
                conn.commit()
                logger.info("✅ Added column: on_hold_reason")
            
            # Fix any existing lowercase enum values
            conn.execute(text("""
                UPDATE vip_registrations 
                SET status = CASE 
                    WHEN status = 'pending' THEN 'PENDING'
                    WHEN status = 'verified' THEN 'VERIFIED' 
                    WHEN status = 'rejected' THEN 'REJECTED'
                    WHEN status = 'on_hold' THEN 'ON_HOLD'
                    ELSE status
                END
                WHERE status IN ('pending', 'verified', 'rejected', 'on_hold')
            """))
            conn.commit()
            logger.info("✅ Fixed enum values to uppercase")
                    
    except Exception as e:
        logger.error(f"Database migration failed: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and bot on startup"""
    # Create database tables
    if Base and engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created")
            
            # Run migrations
            await migrate_database()
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
    
    # Setup bot webhook
    asyncio.create_task(setup_bot_webhook())

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")