"""
Admin Authentication Module
Simple session-based authentication for admin dashboard
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status, Depends, Cookie
from fastapi.responses import RedirectResponse

# Admin credentials from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin@ezymeta.global")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")  # Should be set in production

# If no hash is set, create one for default password "Password123!"
if not ADMIN_PASSWORD_HASH:
    ADMIN_PASSWORD_HASH = hashlib.sha256("Password123!".encode()).hexdigest()
    print(f"⚠️  Using default admin password. Set ADMIN_PASSWORD_HASH environment variable.")
    print(f"Default login: username=admin@ezymeta.global, password=Password123!")

# Session storage (in production, use Redis or database)
admin_sessions = {}

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def create_admin_session(username: str) -> str:
    """Create a new admin session and return session token"""
    session_token = secrets.token_urlsafe(32)
    admin_sessions[session_token] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow()
    }
    return session_token

def verify_admin_session(session_token: Optional[str]) -> Optional[dict]:
    """Verify admin session token and return session data"""
    if not session_token or session_token not in admin_sessions:
        return None
    
    session_data = admin_sessions[session_token]
    
    # Check if session is expired (1 hour)
    if datetime.utcnow() - session_data["created_at"] > timedelta(hours=1):
        del admin_sessions[session_token]
        return None
    
    # Update last activity
    session_data["last_activity"] = datetime.utcnow()
    return session_data

def delete_admin_session(session_token: str):
    """Delete admin session (logout)"""
    if session_token in admin_sessions:
        del admin_sessions[session_token]

async def get_current_admin(admin_session: str = Cookie(None)):
    """Dependency to get current admin user"""
    session_data = verify_admin_session(admin_session)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    return session_data

def admin_login_required(request: Request):
    """Check if admin is logged in, redirect to login if not"""
    admin_session = request.cookies.get("admin_session")
    if not verify_admin_session(admin_session):
        # Redirect to login page
        return RedirectResponse(url="/admin/login", status_code=302)
    return None

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin user"""
    return (username == ADMIN_USERNAME and 
            verify_password(password, ADMIN_PASSWORD_HASH))