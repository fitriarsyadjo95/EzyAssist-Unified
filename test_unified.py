#!/usr/bin/env python3
"""
Test script for EzyAssist Unified System
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_health_endpoint(base_url):
    """Test system health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Bot ready: {data.get('bot_ready')}")
            print(f"   Database ready: {data.get('database_ready')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_registration_form(base_url):
    """Test registration form accessibility"""
    try:
        # Generate a test token (this would normally come from the bot)
        test_token = "test_token_for_demo"
        response = requests.get(f"{base_url}/?token={test_token}", timeout=10)
        
        if response.status_code == 200:
            if "registration" in response.text.lower() or "pendaftaran" in response.text.lower():
                print("✅ Registration form accessible")
                return True
            else:
                print("⚠️ Registration form loaded but content unclear")
                return False
        else:
            print(f"❌ Registration form failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Registration form error: {e}")
        return False

def test_webhook_endpoint(base_url):
    """Test webhook endpoint accessibility"""
    try:
        response = requests.get(f"{base_url}/webhook-test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Webhook endpoint accessible")
            print(f"   Bot ready: {data.get('bot_ready')}")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'OPENAI_API_KEY', 
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def main():
    print("🧪 Testing EzyAssist Unified System\n")
    
    # Default to localhost for testing
    base_url = os.getenv('BASE_URL', 'http://localhost:8000')
    
    if base_url == 'http://localhost:8000':
        print("⚠️  Testing on localhost. Make sure the app is running locally.")
        print("   To test production, set BASE_URL=https://your-app.repl.co\n")
    
    # Test environment variables
    env_test = test_environment_variables()
    print()
    
    # Test system endpoints
    health_test = test_health_endpoint(base_url)
    print()
    
    webhook_test = test_webhook_endpoint(base_url)
    print()
    
    form_test = test_registration_form(base_url)
    print()
    
    # Summary
    print("=" * 50)
    total_tests = 4
    passed_tests = sum([env_test, health_test, webhook_test, form_test])
    
    if passed_tests == total_tests:
        print(f"🎉 All tests passed! ({passed_tests}/{total_tests})")
        print("\n✅ Your unified system is ready for deployment!")
        print("\nNext steps:")
        print("1. Deploy to Replit")
        print("2. Set environment variables in Replit Secrets")
        print("3. Configure Telegram webhook")
        print("4. Test with real users")
    else:
        print(f"⚠️  Some tests failed ({passed_tests}/{total_tests})")
        print("\n🔧 Check the following:")
        if not env_test:
            print("- Set up your .env file with required variables")
        if not health_test:
            print("- Make sure the application is running")
        if not webhook_test:
            print("- Check bot initialization")
        if not form_test:
            print("- Verify templates and static files")
    
    print("=" * 50)

if __name__ == "__main__":
    main()