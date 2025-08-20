#!/usr/bin/env python3
"""
Insert test data via API endpoint
This can be run on Railway where the environment is properly configured
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Test data for 15 registrations
test_registrations = [
    # 10 Verified Users
    {
        "telegram_id": "1234567890",
        "telegram_username": "ahmad_trader", 
        "full_name": "Ahmad Bin Abdullah",
        "email": "ahmad.abdullah@gmail.com",
        "phone_number": "+60123456789",
        "client_id": "EXNESS_MY_001",
        "brokerage_name": "Exness",
        "deposit_amount": 500,
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
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
        "status": "verified"
    },
    
    # 5 Rejected Users
    {
        "telegram_id": "1111111111",
        "telegram_username": "rejected_user1",
        "full_name": "Ali Bin Hassan",
        "email": "ali.hassan@gmail.com",
        "phone_number": "+60191111111",
        "client_id": "INVALID_001",
        "brokerage_name": "Unknown Broker",
        "deposit_amount": 100,
        "status": "rejected"
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
        "status": "rejected"
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
        "status": "rejected"
    },
    {
        "telegram_id": "4444444444",
        "telegram_username": "rejected_user4",
        "full_name": "Wei Ming Tan",
        "email": "weiming@dummy.com", 
        "phone_number": "+60194444444",
        "client_id": "DUMMY_004",
        "brokerage_name": "Fake Markets",
        "deposit_amount": 75,
        "status": "rejected"
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
        "status": "rejected"
    }
]

def create_test_data_endpoint():
    """Create an endpoint to insert test data directly via the application"""
    endpoint_code = '''
@app.post("/admin/create-test-data")
async def create_test_data(admin = Depends(get_current_admin)):
    """Create test registration data (admin only)"""
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")
    
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    test_data = ''' + str(test_registrations) + '''
    
    try:
        created_count = 0
        skipped_count = 0
        
        for user_data in test_data:
            # Check if user already exists
            existing_user = db.query(VipRegistration).filter_by(
                telegram_id=user_data["telegram_id"]
            ).first()
            
            if existing_user:
                skipped_count += 1
                continue
            
            # Calculate registration date (random between 1-20 days ago)
            days_ago = random.randint(1, 20)
            registration_date = datetime.utcnow() - timedelta(days=days_ago)
            
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
        
        return {
            "success": True,
            "message": f"Test data created successfully",
            "created": created_count,
            "skipped": skipped_count,
            "total": len(test_data)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test data: {str(e)}")
    finally:
        db.close()
'''
    
    return endpoint_code

if __name__ == "__main__":
    print("🎯 RentungFX Test Data Generator")
    print("=" * 50)
    print("This script generates code for a test data endpoint.")
    print("Add this endpoint to main.py to create test registrations.")
    print("")
    print("Generated endpoint code:")
    print("=" * 50)
    print(create_test_data_endpoint())
    print("=" * 50)
    print("")
    print("After adding this endpoint:")
    print("1. Deploy to Railway")  
    print("2. Login to admin dashboard")
    print("3. Navigate to /admin/create-test-data")
    print("4. Test data will be created automatically")