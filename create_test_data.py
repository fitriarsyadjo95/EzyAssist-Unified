#!/usr/bin/env python3
"""
Create test registration data for RentungFX system
Generates 15 realistic test registrations: 10 verified, 5 rejected
"""

import os
import sys
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from enum import Enum as PyEnum

# Set required environment variables if not present
if not os.getenv("DATABASE_URL"):
    print("❌ DATABASE_URL environment variable is required")
    print("Please set DATABASE_URL to your PostgreSQL connection string")
    sys.exit(1)

# Create base and models directly to avoid import issues
Base = declarative_base()

class RegistrationStatus(PyEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class VipRegistration(Base):
    __tablename__ = "vip_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, nullable=False, index=True)
    telegram_username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    brokerage_name = Column(String, nullable=False)
    deposit_amount = Column(Integer, nullable=False)
    deposit_proof_1_path = Column(String, nullable=True)
    deposit_proof_2_path = Column(String, nullable=True) 
    deposit_proof_3_path = Column(String, nullable=True)
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status_updated_at = Column(DateTime, nullable=True)
    updated_by_admin = Column(String, nullable=True)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not found")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Connected to database")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Test data for Malaysian users
test_users = [
    # Verified users (10)
    {
        "telegram_id": "1234567890",
        "telegram_username": "ahmad_trader",
        "full_name": "Ahmad Bin Abdullah",
        "email": "ahmad.abdullah@gmail.com",
        "phone_number": "+60123456789",
        "client_id": "EXNESS_MY_001",
        "brokerage_name": "Exness",
        "deposit_amount": 500,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 5
    },
    {
        "telegram_id": "2345678901",
        "telegram_username": "siti_forex",
        "full_name": "Siti Nurhaliza Binti Rashid",
        "email": "siti.nurhaliza@yahoo.com",
        "phone_number": "+60198765432",
        "client_id": "XM_MY_002",
        "brokerage_name": "XM Global",
        "deposit_amount": 750,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 8
    },
    {
        "telegram_id": "3456789012",
        "telegram_username": "mohd_profit",
        "full_name": "Mohammad Hafiz Bin Omar",
        "email": "hafiz.omar@hotmail.com",
        "phone_number": "+60187654321",
        "client_id": "FXCM_MY_003",
        "brokerage_name": "FXCM",
        "deposit_amount": 300,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 12
    },
    {
        "telegram_id": "4567890123",
        "telegram_username": "farah_trading",
        "full_name": "Farah Aisyah Binti Zainal",
        "email": "farah.aisyah@gmail.com",
        "phone_number": "+60176543210",
        "client_id": "IC_MARKETS_004",
        "brokerage_name": "IC Markets",
        "deposit_amount": 1000,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 3
    },
    {
        "telegram_id": "5678901234",
        "telegram_username": "azman_fx",
        "full_name": "Azman Bin Yusof",
        "email": "azman.yusof@gmail.com",
        "phone_number": "+60165432109",
        "client_id": "PEPPERSTONE_005",
        "brokerage_name": "Pepperstone",
        "deposit_amount": 600,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 15
    },
    {
        "telegram_id": "6789012345",
        "telegram_username": "lisa_invest",
        "full_name": "Lisa Tan Wei Ling",
        "email": "lisa.tan@outlook.com",
        "phone_number": "+60154321098",
        "client_id": "AVATRADE_006",
        "brokerage_name": "AvaTrade",
        "deposit_amount": 450,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 7
    },
    {
        "telegram_id": "7890123456",
        "telegram_username": "rizal_capital",
        "full_name": "Rizal Bin Hashim",
        "email": "rizal.hashim@gmail.com",
        "phone_number": "+60143210987",
        "client_id": "FXTM_007",
        "brokerage_name": "FXTM",
        "deposit_amount": 800,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 20
    },
    {
        "telegram_id": "8901234567",
        "telegram_username": "nina_trader",
        "full_name": "Nina Safiya Binti Ahmad",
        "email": "nina.safiya@yahoo.com",
        "phone_number": "+60132109876",
        "client_id": "HOTFOREX_008",
        "brokerage_name": "HotForex",
        "deposit_amount": 550,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 1
    },
    {
        "telegram_id": "9012345678",
        "telegram_username": "daniel_pro",
        "full_name": "Daniel Lim Chee Wei",
        "email": "daniel.lim@gmail.com",
        "phone_number": "+60121098765",
        "client_id": "PLUS500_009",
        "brokerage_name": "Plus500",
        "deposit_amount": 900,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 10
    },
    {
        "telegram_id": "0123456789",
        "telegram_username": "sarah_wealth",
        "full_name": "Sarah Binti Ibrahim",
        "email": "sarah.ibrahim@hotmail.com",
        "phone_number": "+60110987654",
        "client_id": "TICKMILL_010",
        "brokerage_name": "Tickmill",
        "deposit_amount": 650,
        "status": RegistrationStatus.VERIFIED,
        "days_ago": 6
    },
    
    # Rejected users (5)
    {
        "telegram_id": "1111111111",
        "telegram_username": "rejected_user1",
        "full_name": "Ali Bin Hassan",
        "email": "ali.hassan@gmail.com",
        "phone_number": "+60191111111",
        "client_id": "INVALID_001",
        "brokerage_name": "Unknown Broker",
        "deposit_amount": 100,  # Too low
        "status": RegistrationStatus.REJECTED,
        "days_ago": 2
    },
    {
        "telegram_id": "2222222222",
        "telegram_username": "rejected_user2",
        "full_name": "Mira Binti Kamal",
        "email": "fake.email@invalid.com",
        "phone_number": "+60192222222",
        "client_id": "FAKE_002",
        "brokerage_name": "Scam Broker",
        "deposit_amount": 200,
        "status": RegistrationStatus.REJECTED,
        "days_ago": 4
    },
    {
        "telegram_id": "3333333333",
        "telegram_username": "rejected_user3",
        "full_name": "Kumar Ramasamy",
        "email": "kumar.test@test.com",
        "phone_number": "+60193333333",
        "client_id": "TEST_003",
        "brokerage_name": "Test Broker",
        "deposit_amount": 150,
        "status": RegistrationStatus.REJECTED,
        "days_ago": 9
    },
    {
        "telegram_id": "4444444444",
        "telegram_username": "rejected_user4",
        "full_name": "Wei Ming Tan",
        "email": "weiming@dummy.com",
        "phone_number": "+60194444444",
        "client_id": "DUMMY_004",
        "brokerage_name": "Fake Markets",
        "deposit_amount": 75,  # Too low
        "status": RegistrationStatus.REJECTED,
        "days_ago": 11
    },
    {
        "telegram_id": "5555555555",
        "telegram_username": "rejected_user5",
        "full_name": "Raj Singh",
        "email": "raj.singh@invalid.org",
        "phone_number": "+60195555555",
        "client_id": "INVALID_005",
        "brokerage_name": "Non-existent Broker",
        "deposit_amount": 250,
        "status": RegistrationStatus.REJECTED,
        "days_ago": 14
    }
]

def create_test_registrations():
    """Create test registrations in the database"""
    db = SessionLocal()
    created_count = 0
    
    try:
        print(f"🚀 Creating {len(test_users)} test registrations...")
        
        for i, user_data in enumerate(test_users, 1):
            # Calculate registration date
            registration_date = datetime.utcnow() - timedelta(days=user_data["days_ago"])
            
            # Check if user already exists
            existing_user = db.query(VipRegistration).filter_by(
                telegram_id=user_data["telegram_id"]
            ).first()
            
            if existing_user:
                print(f"⚠️  User {user_data['full_name']} already exists, skipping...")
                continue
            
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
                status=user_data["status"],
                ip_address="127.0.0.1",  # Test IP
                user_agent="Mozilla/5.0 (Test Browser)",
                created_at=registration_date,
                status_updated_at=registration_date + timedelta(hours=random.randint(1, 48)),
                updated_by_admin="test_admin"
            )
            
            db.add(registration)
            created_count += 1
            
            status_emoji = "✅" if user_data["status"] == RegistrationStatus.VERIFIED else "❌"
            print(f"{status_emoji} {i:2d}. {user_data['full_name']} ({user_data['status'].value})")
        
        # Commit all changes
        db.commit()
        print(f"\n🎉 Successfully created {created_count} test registrations!")
        
        # Show summary
        verified_count = len([u for u in test_users if u["status"] == RegistrationStatus.VERIFIED])
        rejected_count = len([u for u in test_users if u["status"] == RegistrationStatus.REJECTED])
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Verified: {verified_count}")
        print(f"   ❌ Rejected: {rejected_count}")
        print(f"   📝 Total: {created_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test data: {e}")
        return False
    finally:
        db.close()
    
    return True

def show_current_stats():
    """Show current registration statistics"""
    db = SessionLocal()
    try:
        total = db.query(VipRegistration).count()
        verified = db.query(VipRegistration).filter_by(status=RegistrationStatus.VERIFIED).count()
        pending = db.query(VipRegistration).filter_by(status=RegistrationStatus.PENDING).count()
        rejected = db.query(VipRegistration).filter_by(status=RegistrationStatus.REJECTED).count()
        
        print(f"\n📈 Current Database Statistics:")
        print(f"   📝 Total Registrations: {total}")
        print(f"   ✅ Verified: {verified}")
        print(f"   ⏳ Pending: {pending}")
        print(f"   ❌ Rejected: {rejected}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 RentungFX Test Data Generator")
    print("=" * 50)
    
    # Show current stats
    show_current_stats()
    
    # Create test data
    if create_test_registrations():
        # Show updated stats
        show_current_stats()
        print("\n✨ Test data creation completed successfully!")
        print("📋 You can now view the test registrations in the admin dashboard.")
    else:
        print("\n💥 Test data creation failed!")
        sys.exit(1)