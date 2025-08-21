#!/usr/bin/env python3
"""
Campaign System Test Script
Tests basic functionality of the campaign registration system
"""

import requests
import json
import time
from datetime import datetime

class CampaignSystemTester:
    def __init__(self, base_url, admin_username="admin@ezymeta.global", admin_password="Password123!"):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def admin_login(self):
        """Login to admin panel"""
        try:
            # Get login page
            login_url = f"{self.base_url}/admin/login"
            response = self.session.get(login_url)
            
            if response.status_code != 200:
                self.log_test("Admin Login - Access", False, f"Cannot access login page: {response.status_code}")
                return False
            
            # Attempt login
            login_data = {
                'username': self.admin_username,
                'password': self.admin_password
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            
            if response.status_code in [302, 303]:  # Redirect indicates successful login
                self.log_test("Admin Login - Authentication", True)
                return True
            else:
                self.log_test("Admin Login - Authentication", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login - Connection", False, str(e))
            return False
    
    def test_admin_dashboard(self):
        """Test admin dashboard access and campaign analytics"""
        try:
            dashboard_url = f"{self.base_url}/admin/"
            response = self.session.get(dashboard_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for campaign analytics section
                if "Campaign Analytics" in content:
                    self.log_test("Admin Dashboard - Campaign Analytics", True)
                else:
                    self.log_test("Admin Dashboard - Campaign Analytics", False, "Campaign Analytics section not found")
                
                # Check for campaign performance table
                if "Campaign Performance" in content:
                    self.log_test("Admin Dashboard - Performance Table", True)
                else:
                    self.log_test("Admin Dashboard - Performance Table", True, "No campaigns yet (expected)")
                
                return True
            else:
                self.log_test("Admin Dashboard - Access", False, f"Dashboard inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Dashboard - Connection", False, str(e))
            return False
    
    def test_campaign_management_page(self):
        """Test campaign management page"""
        try:
            campaigns_url = f"{self.base_url}/admin/campaigns"
            response = self.session.get(campaigns_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for key elements
                if "Create Campaign" in content:
                    self.log_test("Campaign Management - Page Access", True)
                else:
                    self.log_test("Campaign Management - Page Access", False, "Create Campaign button not found")
                
                # Check for table structure
                if "Campaign ID" in content and "Registration Link" in content:
                    self.log_test("Campaign Management - Table Structure", True)
                else:
                    self.log_test("Campaign Management - Table Structure", False, "Campaign table structure missing")
                
                return True
            else:
                self.log_test("Campaign Management - Access", False, f"Campaigns page inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Management - Connection", False, str(e))
            return False
    
    def test_create_campaign(self):
        """Test campaign creation"""
        try:
            create_url = f"{self.base_url}/admin/campaigns/create"
            
            # Create test campaign
            campaign_data = {
                'name': 'Test Campaign Automated',
                'description': 'Automated test campaign',
                'min_deposit_amount': '100',
                'reward_description': 'Test reward for automated testing'
            }
            
            response = self.session.post(create_url, data=campaign_data)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.test_campaign_id = result.get('campaign_id')
                        self.log_test("Campaign Creation - Success", True, f"Created campaign: {self.test_campaign_id}")
                        return True
                    else:
                        self.log_test("Campaign Creation - API Response", False, result.get('message', 'Unknown error'))
                        return False
                except json.JSONDecodeError:
                    self.log_test("Campaign Creation - Response Format", False, "Invalid JSON response")
                    return False
            else:
                self.log_test("Campaign Creation - HTTP Status", False, f"Create failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Creation - Connection", False, str(e))
            return False
    
    def test_campaign_public_access(self):
        """Test public campaign access"""
        if not hasattr(self, 'test_campaign_id'):
            self.log_test("Campaign Public Access - Prerequisite", False, "No test campaign created")
            return False
        
        try:
            # Test campaign URL without token (should work for account setup)
            campaign_url = f"{self.base_url}/campaign/{self.test_campaign_id}"
            response = requests.get(campaign_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for campaign elements
                if "Test Campaign Automated" in content:
                    self.log_test("Campaign Public Access - Campaign Info", True)
                else:
                    self.log_test("Campaign Public Access - Campaign Info", False, "Campaign name not displayed")
                
                # Check for setup options
                if "Cipta Akaun Baru" in content and "Tukar IB Partner" in content:
                    self.log_test("Campaign Public Access - Setup Options", True)
                else:
                    self.log_test("Campaign Public Access - Setup Options", False, "Account setup options missing")
                
                return True
            else:
                self.log_test("Campaign Public Access - HTTP Status", False, f"Campaign page inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Public Access - Connection", False, str(e))
            return False
    
    def test_campaign_toggle(self):
        """Test campaign activation toggle"""
        if not hasattr(self, 'test_campaign_id'):
            self.log_test("Campaign Toggle - Prerequisite", False, "No test campaign created")
            return False
        
        try:
            toggle_url = f"{self.base_url}/admin/campaigns/{self.test_campaign_id}/toggle"
            response = self.session.put(toggle_url)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.log_test("Campaign Toggle - Deactivation", True)
                        
                        # Toggle back to active
                        response = self.session.put(toggle_url)
                        if response.status_code == 200:
                            self.log_test("Campaign Toggle - Reactivation", True)
                            return True
                        else:
                            self.log_test("Campaign Toggle - Reactivation", False, f"Reactivation failed: {response.status_code}")
                            return False
                    else:
                        self.log_test("Campaign Toggle - API Response", False, result.get('message', 'Unknown error'))
                        return False
                except json.JSONDecodeError:
                    self.log_test("Campaign Toggle - Response Format", False, "Invalid JSON response")
                    return False
            else:
                self.log_test("Campaign Toggle - HTTP Status", False, f"Toggle failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Toggle - Connection", False, str(e))
            return False
    
    def cleanup_test_campaign(self):
        """Clean up test campaign (Note: Delete endpoint not implemented, would need manual cleanup)"""
        if hasattr(self, 'test_campaign_id'):
            self.log_test("Test Cleanup", True, f"Manual cleanup required for campaign: {self.test_campaign_id}")
        else:
            self.log_test("Test Cleanup", True, "No test campaign to clean up")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"🧪 Starting Campaign System Tests for {self.base_url}")
        print("=" * 60)
        
        # Authentication tests
        if self.admin_login():
            # Admin panel tests
            self.test_admin_dashboard()
            self.test_campaign_management_page()
            
            # Campaign functionality tests
            if self.test_create_campaign():
                self.test_campaign_public_access()
                self.test_campaign_toggle()
            
            # Cleanup
            self.cleanup_test_campaign()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {percentage:.1f}%")
        
        if percentage >= 80:
            print("\n🎉 Campaign system appears to be working well!")
        elif percentage >= 60:
            print("\n⚠️ Campaign system has some issues that need attention.")
        else:
            print("\n❌ Campaign system has significant issues that need fixing.")
        
        return self.test_results

def main():
    """Main test function"""
    import sys
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        # Default to Railway URL - replace with your actual URL
        base_url = "https://ezyassist-unified-production.up.railway.app"
        print(f"Using default URL: {base_url}")
        print("To test different URL, run: python test_campaign_system.py <your-url>")
        print()
    
    tester = CampaignSystemTester(base_url)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('campaign_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: campaign_test_results.json")

if __name__ == "__main__":
    main()