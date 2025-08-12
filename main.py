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
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Text, or_, func, text, Enum, Float, Boolean
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
# Always create Base for model definitions
Base = declarative_base()

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None
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
        admin_notes = Column(Text, nullable=True)
        notes_updated_at = Column(DateTime, nullable=True)
        notes_updated_by = Column(String, nullable=True)
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
                'admin_notes': self.admin_notes,
                'notes_updated_at': self.notes_updated_at.isoformat() if self.notes_updated_at else None,
                'notes_updated_by': self.notes_updated_by,
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

    class RegistrationAuditLog(Base):
        __tablename__ = "registration_audit_logs"
        
        id = Column(Integer, primary_key=True, index=True)
        registration_id = Column(Integer, nullable=False, index=True)
        action = Column(String, nullable=False)  # 'status_change', 'created', 'updated', 'message_sent'
        old_value = Column(String, nullable=True)
        new_value = Column(String, nullable=True)
        admin_user = Column(String, nullable=True)
        details = Column(Text, nullable=True)  # JSON or text with additional details
        timestamp = Column(DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'registration_id': self.registration_id,
                'action': self.action,
                'old_value': self.old_value,
                'new_value': self.new_value,
                'admin_user': self.admin_user,
                'details': self.details,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None
            }

    class ConversationLog(Base):
        __tablename__ = "conversation_logs"
        
        id = Column(Integer, primary_key=True, index=True)
        telegram_id = Column(String, nullable=False, index=True)
        user_message = Column(Text, nullable=False)
        bot_response = Column(Text, nullable=False)
        message_type = Column(String, default="chat")  # 'chat', 'command', 'registration'
        timestamp = Column(DateTime, default=datetime.utcnow, index=True)
        registration_id = Column(Integer, nullable=True, index=True)  # Link to registration if exists
        
        def to_dict(self):
            return {
                'id': self.id,
                'telegram_id': self.telegram_id,
                'user_message': self.user_message,
                'bot_response': self.bot_response,
                'message_type': self.message_type,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'registration_id': self.registration_id
            }

# Admin Settings Model
class AdminSettings(Base):
    __tablename__ = "admin_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String, unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }

# Admin Users Model
class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="admin")  # "super_admin" or "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'last_login': self.last_login.isoformat() if self.last_login else None
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
def generate_registration_token(telegram_id: str, telegram_username: str = "", token_type: str = "initial", registration_id: int = None) -> str:
    """Generate secure registration token with support for different types"""
    try:
        # Set expiry based on token type
        if token_type == "resubmission":
            # 7 days for resubmission tokens
            expiry_minutes = 7 * 24 * 60  # 7 days in minutes
        else:
            # 30 minutes for initial registration tokens
            expiry_minutes = int(os.getenv('FORM_TIMEOUT_MINUTES', 30))
        
        payload = {
            'telegram_id': telegram_id,
            'telegram_username': telegram_username or '',
            'token_type': token_type,
            'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
            'iat': datetime.utcnow()
        }
        
        # Include registration_id for resubmission tokens
        if token_type == "resubmission" and registration_id:
            payload['registration_id'] = registration_id
        
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            raise ValueError("JWT_SECRET_KEY not configured")
            
        token = jwt.encode(payload, secret, algorithm='HS256')
        logger.info(f"Generated {token_type} token for {telegram_id} (expires in {expiry_minutes} minutes)")
        return token
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise

def verify_registration_token(token: str) -> tuple[Optional[str], Optional[str], Optional[dict]]:
    """Verify and decode registration token, returning telegram_id, username, and token data"""
    try:
        secret = os.getenv('JWT_SECRET_KEY')
        if not secret:
            logger.error("JWT_SECRET_KEY not configured")
            return None, None, None
            
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        telegram_id = payload.get('telegram_id')
        telegram_username = payload.get('telegram_username', '')
        
        # Return full payload for additional token information
        return telegram_id, telegram_username, payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None, None, None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None, None, None

def generate_form_hash() -> str:
    """Generate form security hash"""
    return hashlib.sha256(f"{time.time()}{secrets.token_hex(16)}".encode()).hexdigest()[:16]

# Database session dependency
def get_db():
    if not SessionLocal:
        return None
    return SessionLocal()

def add_audit_log(registration_id: int, action: str, old_value: str = None, new_value: str = None, 
                  admin_user: str = None, details: str = None):
    """Add an entry to the registration audit log"""
    if not SessionLocal:
        return
    
    try:
        db = get_db()
        if db:
            audit_entry = RegistrationAuditLog(
                registration_id=registration_id,
                action=action,
                old_value=old_value,
                new_value=new_value,
                admin_user=admin_user,
                details=details
            )
            db.add(audit_entry)
            db.commit()
            logger.info(f"✅ Audit log added: {action} for registration {registration_id}")
            db.close()
    except Exception as e:
        logger.error(f"Failed to add audit log: {e}")
        if db:
            db.close()

def create_initial_audit_logs():
    """Create initial audit log entries for existing registrations"""
    if not SessionLocal:
        return
    
    try:
        db = get_db()
        if db:
            # Get all registrations that don't have any audit logs yet
            registrations = db.query(VipRegistration).all()
            
            for registration in registrations:
                # Check if this registration already has audit logs
                existing_logs = db.query(RegistrationAuditLog).filter(
                    RegistrationAuditLog.registration_id == registration.id
                ).count()
                
                if existing_logs == 0:
                    # Add creation log
                    creation_entry = RegistrationAuditLog(
                        registration_id=registration.id,
                        action="REGISTRATION_CREATED",
                        old_value=None,
                        new_value="pending",
                        admin_user="system",
                        details=f"Registration created by {registration.full_name}",
                        timestamp=registration.created_at or datetime.utcnow()
                    )
                    db.add(creation_entry)
                    
                    # If registration has been updated, add status change log
                    if registration.status != RegistrationStatus.PENDING and registration.status_updated_at:
                        status_entry = RegistrationAuditLog(
                            registration_id=registration.id,
                            action="STATUS_CHANGE",
                            old_value="pending",
                            new_value=registration.status.value,
                            admin_user=registration.updated_by_admin or "admin",
                            details=f"Registration status changed to {registration.status.value}",
                            timestamp=registration.status_updated_at
                        )
                        db.add(status_entry)
            
            db.commit()
            logger.info("✅ Initial audit logs created for existing registrations")
            db.close()
    except Exception as e:
        logger.error(f"Error creating initial audit logs: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

# Admin Settings Helper Functions
def get_admin_setting(key: str, default_value: str = None):
    """Get admin setting value by key"""
    if not SessionLocal:
        return default_value
    
    try:
        db = get_db()
        if db:
            setting = db.query(AdminSettings).filter(
                AdminSettings.setting_key == key
            ).first()
            db.close()
            return setting.setting_value if setting else default_value
    except Exception as e:
        logger.error(f"Error getting admin setting {key}: {e}")
        if 'db' in locals():
            db.close()
        return default_value

def set_admin_setting(key: str, value: str, description: str = None, admin_user: str = None):
    """Set admin setting value"""
    if not SessionLocal:
        return False
    
    try:
        db = get_db()
        if db:
            # Try to get existing setting
            setting = db.query(AdminSettings).filter(
                AdminSettings.setting_key == key
            ).first()
            
            if setting:
                # Update existing setting
                setting.setting_value = value
                setting.updated_at = datetime.utcnow()
                setting.updated_by = admin_user
                if description:
                    setting.description = description
            else:
                # Create new setting
                setting = AdminSettings(
                    setting_key=key,
                    setting_value=value,
                    description=description,
                    updated_by=admin_user
                )
                db.add(setting)
            
            db.commit()
            db.close()
            logger.info(f"✅ Admin setting updated: {key} = {value}")
            return True
    except Exception as e:
        logger.error(f"Error setting admin setting {key}: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def initialize_default_settings():
    """Initialize default admin settings"""
    default_settings = [
        {
            'key': 'vip_group_link',
            'value': 'https://t.me/+VIPGroupDefault',
            'description': 'VIP Telegram group link for verified users'
        },
        {
            'key': 'admin_notification_enabled',
            'value': 'true',
            'description': 'Enable admin notifications for new registrations'
        },
        {
            'key': 'notification_recipient',
            'value': '@admin',
            'description': 'Telegram username or chat ID to receive notifications'
        },
        {
            'key': 'auto_approval_enabled',
            'value': 'false',
            'description': 'Enable automatic approval of registrations'
        }
    ]
    
    for setting in default_settings:
        # Only set if doesn't exist
        if get_admin_setting(setting['key']) is None:
            set_admin_setting(
                setting['key'],
                setting['value'],
                setting['description'],
                'system'
            )

# Admin User Management Functions
def create_admin_user(username: str, email: str, password: str, full_name: str, 
                     role: str = "admin", created_by: str = None):
    """Create a new admin user"""
    if not SessionLocal:
        return False, "Database not available"
    
    try:
        db = get_db()
        if db:
            # Check if username or email already exists
            existing = db.query(AdminUser).filter(
                (AdminUser.username == username) | (AdminUser.email == email)
            ).first()
            
            if existing:
                db.close()
                return False, "Username or email already exists"
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create new admin user
            admin_user = AdminUser(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                created_by=created_by
            )
            
            db.add(admin_user)
            db.commit()
            db.close()
            
            logger.info(f"✅ Admin user created: {username} by {created_by}")
            return True, "Admin user created successfully"
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False, f"Error creating admin user: {str(e)}"

def get_all_admin_users():
    """Get all admin users"""
    if not SessionLocal:
        return []
    
    try:
        db = get_db()
        if db:
            admin_users = db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()
            db.close()
            return [user.to_dict() for user in admin_users]
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        if 'db' in locals():
            db.close()
        return []

def update_admin_user(user_id: int, **updates):
    """Update admin user"""
    if not SessionLocal:
        return False, "Database not available"
    
    try:
        db = get_db()
        if db:
            admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
            if not admin_user:
                db.close()
                return False, "Admin user not found"
            
            # Update fields
            for key, value in updates.items():
                if hasattr(admin_user, key):
                    if key == 'password' and value:
                        admin_user.password_hash = hashlib.sha256(value.encode()).hexdigest()
                    else:
                        setattr(admin_user, key, value)
            
            db.commit()
            db.close()
            return True, "Admin user updated successfully"
            
    except Exception as e:
        logger.error(f"Error updating admin user: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False, f"Error updating admin user: {str(e)}"

def delete_admin_user(user_id: int):
    """Delete admin user"""
    if not SessionLocal:
        return False, "Database not available"
    
    try:
        db = get_db()
        if db:
            admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
            if not admin_user:
                db.close()
                return False, "Admin user not found"
            
            db.delete(admin_user)
            db.commit()
            db.close()
            return True, "Admin user deleted successfully"
            
    except Exception as e:
        logger.error(f"Error deleting admin user: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False, f"Error deleting admin user: {str(e)}"

def authenticate_admin_user(username: str, password: str):
    """Authenticate admin user against database"""
    if not SessionLocal:
        return None
    
    try:
        db = get_db()
        if db:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            admin_user = db.query(AdminUser).filter(
                AdminUser.username == username,
                AdminUser.password_hash == password_hash,
                AdminUser.is_active == True
            ).first()
            
            if admin_user:
                # Update last login
                admin_user.last_login = datetime.utcnow()
                db.commit()
                user_data = admin_user.to_dict()
                db.close()
                return user_data
            
            db.close()
            return None
            
    except Exception as e:
        logger.error(f"Error authenticating admin user: {e}")
        if 'db' in locals():
            db.close()
        return None

def initialize_default_admin():
    """Initialize default super admin if no admin users exist"""
    if not SessionLocal:
        return
    
    try:
        db = get_db()
        if db:
            # Check if any admin users exist
            admin_count = db.query(AdminUser).count()
            
            if admin_count == 0:
                # Create default super admin
                password_hash = hashlib.sha256("Password123!".encode()).hexdigest()
                default_admin = AdminUser(
                    username="admin@ezymeta.global",
                    email="admin@ezymeta.global",
                    password_hash=password_hash,
                    full_name="System Administrator",
                    role="super_admin",
                    created_by="system"
                )
                
                db.add(default_admin)
                db.commit()
                logger.info("✅ Default super admin created: admin@ezymeta.global")
            
            db.close()
            
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

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
        
        # Log command to database
        self.log_conversation(telegram_id, "/start", welcome_message, "command")

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
            
            # Log command to database
            self.log_conversation(telegram_id, "/register", register_message, "command")
            
        except Exception as e:
            logger.error(f"Registration command error: {e}")
            error_message = "Maaf, ada masalah teknikal. Sila cuba lagi dalam beberapa minit."
            await update.message.reply_text(error_message)
            
            # Log error command to database
            self.log_conversation(telegram_id, "/register", error_message, "command")

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
        
        # Log command to database
        self.log_conversation(telegram_id, "/clear", clear_message, "command")

    def log_conversation(self, telegram_id: str, user_message: str, bot_response: str, message_type: str = "chat"):
        """Log conversation to database"""
        if not SessionLocal:
            return
        
        try:
            db = get_db()
            if db:
                # Try to find matching registration
                registration = db.query(VipRegistration).filter(
                    VipRegistration.telegram_id == telegram_id
                ).first()
                
                # Create conversation log entry
                conversation_log = ConversationLog(
                    telegram_id=telegram_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    message_type=message_type,
                    registration_id=registration.id if registration else None
                )
                
                db.add(conversation_log)
                db.commit()
                db.close()
                logger.debug(f"✅ Conversation logged for {telegram_id}")
        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()

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
        
        # Log conversation to database
        self.log_conversation(telegram_id, message_text, response, "chat")

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
async def registration_entry(request: Request, token: str = None):
    """Registration entry point - redirects to account setup (Step 1)"""
    if not token:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Missing registration token. Please use the link from the Telegram bot.",
            "translations": TRANSLATIONS['ms']
        })
    
    # Redirect to account setup step
    return RedirectResponse(url=f"/account-setup?token={token}", status_code=302)

@app.get("/account-setup", response_class=HTMLResponse)
async def account_setup_page(request: Request, token: str = None):
    """Account setup page (Step 1)"""
    if not token:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Missing registration token. Please use the link from the Telegram bot.",
            "translations": TRANSLATIONS['ms']
        })
    
    telegram_id, telegram_username, token_data = verify_registration_token(token)
    if not telegram_id:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid or expired registration token",
            "translations": TRANSLATIONS['ms']
        })
    
    return templates.TemplateResponse("account_setup.html", {
        "request": request,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "token": token,
        "translations": TRANSLATIONS['ms']
    })

@app.post("/account-setup/continue")
async def account_setup_continue(request: Request, token: str = Form(...)):
    """Continue from account setup to registration form (Step 2)"""
    return RedirectResponse(url=f"/registration-form?token={token}", status_code=302)

@app.get("/registration-form", response_class=HTMLResponse)
async def registration_form(request: Request, token: str = None):
    """Registration form page (Step 2)"""
    if not token:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Missing registration token. Please use the link from the Telegram bot.",
            "translations": TRANSLATIONS['ms']
        })
    
    telegram_id, telegram_username, token_data = verify_registration_token(token)
    if not telegram_id:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid or expired registration token",
            "translations": TRANSLATIONS['ms']
        })
    
    # Get token type and registration data for resubmissions
    token_type = token_data.get('token_type', 'initial') if token_data else 'initial'
    existing_registration = None
    
    if SessionLocal:
        db = get_db()
        if db:
            # For resubmission tokens, get existing registration data
            if token_type == "resubmission" and token_data.get('registration_id'):
                existing_registration = db.query(VipRegistration).filter_by(
                    id=token_data['registration_id']
                ).first()
            else:
                # For initial tokens, check if already registered
                existing = db.query(VipRegistration).filter_by(telegram_id=telegram_id).first()
                if existing:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error_message": TRANSLATIONS['ms']['already_registered'],
                        "translations": TRANSLATIONS['ms'],
                        "lang": "ms"
                    })
            db.close()
    
    form_hash = generate_form_hash()
    template_data = {
        "request": request,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "token": token,
        "form_hash": form_hash,
        "translations": TRANSLATIONS['ms'],
        "token_type": token_type,
        "existing_registration": existing_registration.to_dict() if existing_registration else None,
        "is_resubmission": token_type == "resubmission"
    }
    
    return templates.TemplateResponse("simple_form.html", template_data)

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
    telegram_id, telegram_username, token_data = verify_registration_token(token)
    if not telegram_id:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Token tidak sah atau telah tamat tempoh",
            "translations": TRANSLATIONS['ms']
        })
    
    # Determine if this is a resubmission
    token_type = token_data.get('token_type', 'initial') if token_data else 'initial'
    is_resubmission = token_type == "resubmission"
    registration_id = token_data.get('registration_id') if token_data else None
    
    # Force brokerage to OctaFX for the new two-step flow
    brokerage_name = "OctaFX"
    logger.info(f"✅ Brokerage forced to: {brokerage_name}")
    
    # Validate required fields (excluding brokerage since it's auto-set)
    if not all([full_name.strip(), email.strip(), phone_number.strip(), deposit_amount.strip(), client_id.strip()]):
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
                if is_resubmission and registration_id:
                    # Update existing registration
                    existing_registration = db.query(VipRegistration).filter_by(id=registration_id).first()
                    if existing_registration:
                        # Update fields
                        existing_registration.full_name = full_name.strip()
                        existing_registration.email = email.strip()
                        existing_registration.phone_number = phone_number.strip()
                        existing_registration.brokerage_name = brokerage_name.strip()
                        existing_registration.deposit_amount = deposit_amount.strip()
                        existing_registration.client_id = client_id.strip()
                        
                        # Update file paths only if new files were uploaded
                        if deposit_proof_1_path:
                            existing_registration.deposit_proof_1_path = deposit_proof_1_path
                        if deposit_proof_2_path:
                            existing_registration.deposit_proof_2_path = deposit_proof_2_path
                        if deposit_proof_3_path:
                            existing_registration.deposit_proof_3_path = deposit_proof_3_path
                        
                        # Reset status to pending for re-review
                        existing_registration.status = RegistrationStatus.PENDING
                        existing_registration.on_hold_reason = None
                        existing_registration.custom_message = None
                        existing_registration.status_updated_at = datetime.utcnow()
                        
                        db.commit()
                        logger.info(f"✅ Registration updated for {full_name} (ID: {registration_id})")
                        
                        # Create audit log
                        add_audit_log(
                            registration_id=registration_id,
                            action="RESUBMITTED",
                            new_value="User resubmitted registration data",
                            details="Registration updated via resubmission form"
                        )
                        
                        # Send pending notification to user via bot
                        await send_registration_pending(telegram_id, existing_registration.to_dict())
                        
                        # Notify admin of resubmission
                        await send_admin_notification(existing_registration.to_dict())
                        
                    else:
                        logger.error(f"Registration {registration_id} not found for resubmission")
                        return templates.TemplateResponse("error.html", {
                            "request": request,
                            "error_message": "Pendaftaran tidak dijumpai",
                            "translations": TRANSLATIONS['ms']
                        })
                else:
                    # Create new registration
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
                    logger.info(f"✅ New registration saved for {full_name}")
                    
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
            finally:
                db.close()
    
    # Redirect to success page
    return RedirectResponse(url=f"/success?token={token}", status_code=303)

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, token: str = None):
    """Registration success page"""
    telegram_id = None
    telegram_username = None
    
    if token:
        telegram_id, telegram_username, token_data = verify_registration_token(token)
    
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
            # Get VIP group link from settings
            vip_group_link = get_admin_setting('vip_group_link', 'https://t.me/ezyassist_vip')
            
            vip_message = (
                f"🎉 Berita Baik, VIP akses anda diluluskan!\n\n"
                f"Hai {registration_data['full_name']},\n\n"
                f"✅ Pendaftaran VIP anda telah DILULUSKAN!\n"
                f"🔥 Anda kini boleh akses group VIP kami.\n\n"
                f"🔗 VIP Group Link: {vip_group_link}\n\n"
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
    """Send registration on hold message with custom admin message and resubmission link"""
    try:
        if bot_instance and bot_instance.application:
            # Generate resubmission token (7 days expiry)
            resubmission_token = generate_registration_token(
                telegram_id, 
                registration_data.get('telegram_username', ''),
                token_type="resubmission",
                registration_id=registration_data.get('id')
            )
            
            # Get base URL from environment
            base_url = os.getenv('BASE_URL', 'https://ezyassist-unified-production.up.railway.app')
            resubmission_url = f"{base_url}/?token={resubmission_token}"
            
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
                f"🔄 **Untuk mengemas kini pendaftaran anda:**\n"
                f"👉 {resubmission_url}\n\n"
                f"⏰ Link ini aktif selama 7 hari.\n"
                f"📝 Borang akan diisi dengan data anda yang sedia ada - anda hanya perlu mengemas kini bahagian yang diperlukan.\n\n"
                f"📱 Pastikan phone {registration_data.get('phone_number', 'N/A')} aktif untuk makluman!\n\n"
                f"🙏 Terima kasih atas kerjasama anda."
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=telegram_id, 
                text=on_hold_message
            )
            logger.info(f"✅ Registration on hold message with resubmission link sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send on hold message: {e}")

async def send_admin_notification(registration_data: dict):
    """Send notification to admin"""
    try:
        # Check if notifications are enabled
        if get_admin_setting('admin_notification_enabled', 'false') != 'true':
            logger.info("Admin notifications are disabled")
            return
            
        # Get notification recipient from settings
        notification_recipient = get_admin_setting('notification_recipient', None)
        
        # Fall back to default admin_id if no recipient configured
        if not notification_recipient:
            if bot_instance and bot_instance.admin_id:
                notification_recipient = bot_instance.admin_id
            else:
                logger.warning("No notification recipient configured")
                return
        
        if bot_instance and bot_instance.application:
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
            
            # Handle both username and chat_id formats
            chat_id = notification_recipient
            if notification_recipient.startswith('@'):
                # For usernames, we need to use the username as-is
                chat_id = notification_recipient
            else:
                # For numeric chat IDs, ensure it's an integer
                try:
                    chat_id = int(notification_recipient)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid chat_id format: {notification_recipient}")
                    return
            
            await bot_instance.application.bot.send_message(
                chat_id=chat_id, 
                text=admin_message
            )
            logger.info(f"✅ Admin notification sent to {notification_recipient}")
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
                stats = {
                    "error": "Could not load statistics",
                    "total_registrations": 0,
                    "recent_registrations": 0,
                    "pending_count": 0,
                    "verified_count": 0,
                    "rejected_count": 0,
                    "on_hold_count": 0,
                    "broker_stats": []
                }
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

@app.get("/admin/registrations/{registration_id}/audit-logs")
async def get_registration_audit_logs(
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """Get audit logs for a specific registration"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Verify registration exists
        registration = db.query(VipRegistration).filter(
            VipRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Get audit logs for this registration
        audit_logs = db.query(RegistrationAuditLog).filter(
            RegistrationAuditLog.registration_id == registration_id
        ).order_by(RegistrationAuditLog.timestamp.desc()).all()
        
        # Convert to dict format
        logs_data = []
        for log in audit_logs:
            logs_data.append({
                "id": log.id,
                "action": log.action,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "admin_user": log.admin_user,
                "details": log.details,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if log.timestamp else None
            })
        
        return JSONResponse(content={"audit_logs": logs_data})
        
    except Exception as e:
        logger.error(f"Error getting audit logs for registration {registration_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")
    finally:
        db.close()

@app.post("/admin/create-initial-audit-logs")
async def create_audit_logs_endpoint(admin = Depends(get_current_admin)):
    """Create initial audit logs for existing registrations - Admin endpoint"""
    try:
        create_initial_audit_logs()
        return JSONResponse(content={
            "status": "success",
            "message": "Initial audit logs created successfully"
        })
    except Exception as e:
        logger.error(f"Error creating initial audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to create initial audit logs")

@app.get("/admin/conversations/{registration_id}", response_class=HTMLResponse)
async def view_conversations(
    request: Request, 
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """View conversation history for a specific registration"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        db = get_db()
        
        # Get registration details
        registration = db.query(VipRegistration).filter(
            VipRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Get conversation history
        conversations = db.query(ConversationLog).filter(
            or_(
                ConversationLog.registration_id == registration_id,
                ConversationLog.telegram_id == registration.telegram_id
            )
        ).order_by(ConversationLog.timestamp.asc()).all()
        
        db.close()
        
        return templates.TemplateResponse("admin/conversations.html", {
            "request": request,
            "registration": registration,
            "conversations": conversations,
            "conversation_count": len(conversations)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversations for registration {registration_id}: {e}")
        if 'db' in locals():
            db.close()
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request, admin = Depends(get_current_admin)):
    """Admin settings page"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    # Get current settings
    settings = {}
    if SessionLocal:
        try:
            db = get_db()
            if db:
                all_settings = db.query(AdminSettings).all()
                for setting in all_settings:
                    settings[setting.setting_key] = setting.setting_value
                db.close()
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            if 'db' in locals():
                db.close()
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "admin": admin,
        "settings": settings
    })

@app.post("/admin/settings/save")
async def save_admin_settings(
    request: Request,
    admin = Depends(get_current_admin)
):
    """Save admin settings"""
    try:
        # Get request body
        body = await request.json()
        admin_username = admin.get('username', 'admin')
        
        # Define allowed settings with their descriptions
        allowed_settings = {
            'vip_group_link': 'VIP Telegram group link for verified users',
            'admin_notification_enabled': 'Enable admin notifications for new registrations',
            'notification_recipient': 'Telegram username or chat ID to receive notifications',
            'auto_approval_enabled': 'Enable automatic approval of registrations'
        }
        
        success_count = 0
        for key, value in body.items():
            if key in allowed_settings:
                if set_admin_setting(key, str(value), allowed_settings[key], admin_username):
                    success_count += 1
                else:
                    logger.error(f"Failed to save setting: {key}")
        
        if success_count == len(body):
            return JSONResponse(content={
                "status": "success",
                "message": f"All {success_count} settings saved successfully"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Only {success_count} out of {len(body)} settings were saved"
                }
            )
            
    except Exception as e:
        logger.error(f"Error saving admin settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save settings")

# Pydantic models for admin user management
class AdminUserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "admin"
    is_active: bool = True

class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/admin/admin-users", response_class=HTMLResponse)
async def admin_users_page(request: Request, admin = Depends(get_current_admin)):
    """Admin users management page"""
    # Check for redirect
    redirect_check = admin_login_required(request)
    if redirect_check:
        return redirect_check
    
    return templates.TemplateResponse("admin/admin_users.html", {
        "request": request,
        "admin": admin
    })

@app.get("/admin/admin-users/list")
async def list_admin_users(admin = Depends(get_current_admin)):
    """Get all admin users"""
    try:
        admin_users = get_all_admin_users()
        return JSONResponse(content={"admin_users": admin_users})
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin users")

@app.get("/admin/admin-users/{user_id}")
async def get_admin_user(user_id: int, admin = Depends(get_current_admin)):
    """Get specific admin user"""
    try:
        admin_users = get_all_admin_users()
        user = next((u for u in admin_users if u['id'] == user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="Admin user not found")
        
        return JSONResponse(content={"admin_user": user})
    except Exception as e:
        logger.error(f"Error getting admin user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin user")

@app.post("/admin/admin-users/create")
async def create_admin_user_endpoint(
    admin_data: AdminUserCreate,
    admin = Depends(get_current_admin)
):
    """Create new admin user"""
    try:
        success, message = create_admin_user(
            username=admin_data.username,
            email=admin_data.email,
            password=admin_data.password,
            full_name=admin_data.full_name,
            role=admin_data.role,
            created_by=admin.get('username', 'admin')
        )
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": message
            })
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create admin user")

@app.put("/admin/admin-users/{user_id}/update")
async def update_admin_user_endpoint(
    user_id: int,
    admin_data: AdminUserUpdate,
    admin = Depends(get_current_admin)
):
    """Update admin user"""
    try:
        # Convert to dict and remove None values
        updates = {k: v for k, v in admin_data.dict().items() if v is not None}
        
        success, message = update_admin_user(user_id, **updates)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": message
            })
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Error updating admin user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update admin user")

@app.delete("/admin/admin-users/{user_id}/delete")
async def delete_admin_user_endpoint(
    user_id: int,
    admin = Depends(get_current_admin)
):
    """Delete admin user"""
    try:
        success, message = delete_admin_user(user_id)
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": message
            })
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Error deleting admin user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete admin user")

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
        
        # Store old status for audit log
        old_status = registration.status.value if registration.status else 'unknown'
        
        # Update status
        registration.status = RegistrationStatus.VERIFIED
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        
        db.commit()
        
        # Add audit log entry
        add_audit_log(
            registration_id=registration_id,
            action="STATUS_CHANGE",
            old_value=old_status,
            new_value="verified",
            admin_user=admin.get('username', 'admin'),
            details="Registration verified and VIP access granted"
        )
        
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
        
        # Store old status for audit log
        old_status = registration.status.value if registration.status else 'unknown'
        
        # Update status
        registration.status = RegistrationStatus.REJECTED
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        
        db.commit()
        
        # Add audit log entry
        add_audit_log(
            registration_id=registration_id,
            action="STATUS_CHANGE",
            old_value=old_status,
            new_value="rejected",
            admin_user=admin.get('username', 'admin'),
            details="Registration rejected and user notified"
        )
        
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
        
        # Store old values for audit log
        old_status = registration.status.value if registration.status else 'unknown'
        old_message = registration.custom_message or ''
        old_reason = registration.on_hold_reason or ''
        
        # Update status
        registration.status = RegistrationStatus.ON_HOLD
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_admin = admin.get('username', 'admin')
        registration.custom_message = request.custom_message.strip()
        registration.on_hold_reason = request.hold_reason.strip() if request.hold_reason else None
        
        db.commit()
        
        # Add audit log entries
        add_audit_log(
            registration_id=registration_id,
            action="STATUS_CHANGE",
            old_value=old_status,
            new_value="on_hold",
            admin_user=admin.get('username', 'admin'),
            details=f"Registration put on hold. Reason: {request.hold_reason or 'None'}"
        )
        
        add_audit_log(
            registration_id=registration_id,
            action="CUSTOM_MESSAGE",
            old_value=old_message,
            new_value=request.custom_message.strip(),
            admin_user=admin.get('username', 'admin'),
            details="Custom message updated for user notification"
        )
        
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

@app.post("/admin/registrations/{registration_id}/send-resubmission-link")
async def send_resubmission_link(
    registration_id: int,
    admin = Depends(get_current_admin)
):
    """Send resubmission link to user"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Get registration
        registration = db.query(VipRegistration).filter(VipRegistration.id == registration_id).first()
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Generate resubmission token
        resubmission_token = generate_registration_token(
            registration.telegram_id,
            registration.telegram_username or '',
            token_type="resubmission",
            registration_id=registration_id
        )
        
        # Get base URL from environment
        base_url = os.getenv('BASE_URL', 'https://ezyassist-unified-production.up.railway.app')
        resubmission_url = f"{base_url}/?token={resubmission_token}"
        
        # Send message to user
        if bot_instance and bot_instance.application:
            message = (
                f"🔄 Link Kemas Kini Pendaftaran VIP\n\n"
                f"Hai {registration.full_name},\n\n"
                f"Berikut adalah link untuk mengemas kini pendaftaran VIP anda:\n\n"
                f"👉 {resubmission_url}\n\n"
                f"⏰ Link ini aktif selama 7 hari.\n"
                f"📝 Borang akan diisi dengan data anda yang sedia ada.\n\n"
                f"🙏 Terima kasih!"
            )
            
            await bot_instance.application.bot.send_message(
                chat_id=registration.telegram_id,
                text=message
            )
        
        # Create audit log
        add_audit_log(
            registration_id=registration_id,
            action="RESUBMISSION_LINK_SENT",
            admin_user=admin.get('username'),
            details="Admin manually sent resubmission link to user"
        )
        
        logger.info(f"✅ Resubmission link sent for registration {registration_id} by {admin.get('username')}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Resubmission link sent to user successfully"
        })
        
    except Exception as e:
        logger.error(f"Error sending resubmission link for registration {registration_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send resubmission link")
    finally:
        db.close()

# Pydantic model for admin notes
class AdminNotesRequest(BaseModel):
    notes: str

@app.post("/admin/registrations/{registration_id}/notes")
async def update_admin_notes(
    registration_id: int,
    request: AdminNotesRequest,
    admin = Depends(get_current_admin)
):
    """Update admin notes for a registration"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        # Validate notes length
        if len(request.notes) > 1000:
            raise HTTPException(status_code=400, detail="Notes must not exceed 1000 characters")
        
        # Get registration
        registration = db.query(VipRegistration).filter(VipRegistration.id == registration_id).first()
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Update notes
        old_notes = registration.admin_notes
        registration.admin_notes = request.notes if request.notes.strip() else None
        registration.notes_updated_at = datetime.utcnow()
        registration.notes_updated_by = admin.get('username')
        
        db.commit()
        
        # Create audit log
        add_audit_log(
            registration_id=registration_id,
            action="ADMIN_NOTES_UPDATED",
            old_value=old_notes[:100] + "..." if old_notes and len(old_notes) > 100 else old_notes,
            new_value=request.notes[:100] + "..." if len(request.notes) > 100 else request.notes,
            admin_user=admin.get('username'),
            details=f"Admin notes {'updated' if old_notes else 'added'} by {admin.get('username')}"
        )
        
        logger.info(f"✅ Admin notes updated for registration {registration_id} by {admin.get('username')}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Admin notes updated successfully",
            "notes_updated_at": registration.notes_updated_at.isoformat(),
            "notes_updated_by": registration.notes_updated_by
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating admin notes for registration {registration_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update admin notes")
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
            
            # Check for admin notes columns
            notes_result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'vip_registrations' 
                AND column_name IN ('admin_notes', 'notes_updated_at', 'notes_updated_by')
            """))
            existing_notes_columns = [row[0] for row in notes_result]
            
            # Add admin_notes column if missing
            if 'admin_notes' not in existing_notes_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN admin_notes TEXT
                """))
                conn.commit()
                logger.info("✅ Added column: admin_notes")
            
            # Add notes_updated_at column if missing
            if 'notes_updated_at' not in existing_notes_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN notes_updated_at TIMESTAMP
                """))
                conn.commit()
                logger.info("✅ Added column: notes_updated_at")
            
            # Add notes_updated_by column if missing
            if 'notes_updated_by' not in existing_notes_columns:
                conn.execute(text("""
                    ALTER TABLE vip_registrations 
                    ADD COLUMN notes_updated_by VARCHAR
                """))
                conn.commit()
                logger.info("✅ Added column: notes_updated_by")
            
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
            
            # Check if audit log table exists
            audit_table_result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'registration_audit_logs'
                )
            """))
            audit_table_exists = audit_table_result.scalar()
            
            if not audit_table_exists:
                conn.execute(text("""
                    CREATE TABLE registration_audit_logs (
                        id SERIAL PRIMARY KEY,
                        registration_id INTEGER NOT NULL,
                        action VARCHAR NOT NULL,
                        old_value VARCHAR,
                        new_value VARCHAR,
                        admin_user VARCHAR,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("""
                    CREATE INDEX idx_registration_audit_logs_registration_id 
                    ON registration_audit_logs(registration_id)
                """))
                conn.commit()
                logger.info("✅ Created registration_audit_logs table")
                    
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
            
            # Initialize default settings
            initialize_default_settings()
            
            # Initialize default admin
            initialize_default_admin()
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
    
    # Setup bot webhook
    asyncio.create_task(setup_bot_webhook())

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")