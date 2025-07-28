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
import uuid
import shutil
from pathlib import Path
from functools import wraps

# FastAPI and web components
from fastapi import FastAPI, Request, Form, HTTPException, status, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Telegram bot components
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Database and external services
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, or_, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import requests
import uvicorn

# AI and conversation
from conversation_engine import ConversationEngine
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
    return SessionLocal()

# Telegram Bot Class
class EzyAssistBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        self.conversation_engine = ConversationEngine()
        self.engagement_scores = {}
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
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

        # Update last seen (removed Supabase dependency)

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
            max_age=86400,  # 24 hours
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
                
                # Registrations by broker
                broker_stats = db.query(
                    VipRegistration.brokerage_name,
                    func.count(VipRegistration.id).label('count')
                ).group_by(VipRegistration.brokerage_name).all()
                
                stats = {
                    "total_registrations": total_registrations,
                    "recent_registrations": recent_registrations,
                    "broker_stats": broker_stats
                }
            except Exception as e:
                logger.error(f"Error getting admin stats: {e}")
                stats = {"error": "Could not load statistics"}
            finally:
                db.close()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "stats": stats
    })

@app.get("/admin/registrations", response_class=HTMLResponse)
async def admin_registrations_list(
    request: Request, 
    page: int = 1, 
    search: str = "",
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
        "search": search
    })

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