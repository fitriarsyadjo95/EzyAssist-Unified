#!/usr/bin/env python3
"""
Script to import CSV data to the admin panel
"""
import requests
import sys
import os
from pathlib import Path

def import_csv_to_admin(csv_file_path, base_url="http://localhost:8080", username="admin@ezymeta.global", password=None):
    """
    Import CSV file to admin panel
    """
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: File {csv_file_path} not found")
        return False
    
    # If password not provided, use environment variable or default
    if not password:
        password = os.getenv('ADMIN_PASSWORD', 'Password123!')  # Default password if not set
    
    # Step 1: Login to get session cookie
    login_url = f"{base_url}/admin/login"
    login_data = {
        'username': username,
        'password': password
    }
    
    session = requests.Session()
    
    print(f"🔐 Logging in as {username}...")
    login_response = session.post(login_url, data=login_data, allow_redirects=False)
    
    if login_response.status_code not in [200, 302, 303]:
        print(f"❌ Login failed. Status code: {login_response.status_code}")
        print("Please check your admin credentials.")
        return False
    
    # Check if we got a session cookie
    if 'admin_session' not in session.cookies:
        print("❌ No admin_session cookie received. Login may have failed.")
        # Try to proceed anyway as redirect might work
        pass
    
    print("✅ Login successful")
    
    # Step 2: Upload the CSV file
    import_url = f"{base_url}/admin/registrations/import"
    
    print(f"📤 Uploading {csv_file_path}...")
    
    with open(csv_file_path, 'rb') as f:
        files = {'file': (Path(csv_file_path).name, f, 'text/csv')}
        
        try:
            response = session.post(import_url, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Import completed successfully!")
                print(f"📊 Import Results:")
                print(f"   Total rows: {result.get('total_rows', 0)}")
                print(f"   Successful: {result.get('successful', 0)}")
                print(f"   Duplicates: {result.get('duplicates', 0)}")
                print(f"   Errors: {result.get('errors', 0)}")
                
                if result.get('error_details'):
                    print("\n⚠️ Error Details:")
                    for error in result['error_details'][:10]:  # Show first 10 errors
                        print(f"   - {error}")
                    if len(result['error_details']) > 10:
                        print(f"   ... and {len(result['error_details']) - 10} more errors")
                
                return True
            else:
                print(f"❌ Import failed. Status code: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False

if __name__ == "__main__":
    # File to import
    csv_file = "Formatted_Client_Data.csv"
    
    # Check if custom password provided as argument
    password = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🚀 Starting CSV Import to Admin Panel")
    print("=" * 50)
    
    # Import the file
    success = import_csv_to_admin(csv_file, password=password)
    
    if success:
        print("\n🎉 Import process completed successfully!")
        print("You can now view the imported data in the admin panel:")
        print("http://localhost:8080/admin/registrations")
    else:
        print("\n❌ Import process failed.")
        print("Please check the error messages above and try again.")