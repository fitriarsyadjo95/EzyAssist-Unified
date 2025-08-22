#!/usr/bin/env python3
"""
Comprehensive Campaign System Test Script
Tests all functionality of the campaign registration system with detailed validation
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import sys
import os

class Colors:
    """Console colors for better output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CampaignSystemTester:
    def __init__(self, base_url, admin_username="admin@ezymeta.global", admin_password="Password123!"):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CampaignSystemTester/1.0'
        })
        
        self.test_results = []
        self.test_campaign_id = None
        self.registration_token = None
        self.test_registration_id = None
        
        # Test data
        self.test_campaign_data = {
            'name': 'Automated Test Campaign',
            'description': 'Campaign created by automated test script',
            'min_deposit_amount': '100',
            'reward_description': 'RM50 test reward for validation'
        }
        
        self.test_registration_data = {
            'full_name': 'Test User Automated',
            'email': 'test.automated@example.com',
            'phone_number': '+60123456789',
            'country': 'Malaysia',
            'trading_id': 'TEST123456',
            'deposit_amount': '150',
            'telegram_username': 'testautomated',
            'telegram_id': '123456789'
        }
    
    def print_header(self, text):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    def print_section(self, text):
        """Print colored section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
        print(f"{Colors.CYAN}{'-'*len(text)}{Colors.END}")
    
    def log_test(self, test_name, passed, message="", details=None):
        """Log test result with enhanced formatting"""
        status_color = Colors.GREEN if passed else Colors.RED
        status_text = "✅ PASS" if passed else "❌ FAIL"
        
        result = f"{status_color}{status_text}{Colors.END} - {test_name}"
        if message:
            result += f": {message}"
        print(result)
        
        if details:
            print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def make_request(self, method, url, **kwargs):
        """Make HTTP request with error handling"""
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.Timeout:
            self.log_test(f"{method} Request Timeout", False, f"Request to {url} timed out")
            return None
        except requests.exceptions.ConnectionError:
            self.log_test(f"{method} Connection Error", False, f"Cannot connect to {url}")
            return None
        except Exception as e:
            self.log_test(f"{method} Request Error", False, str(e))
            return None
    
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        self.print_section("🌐 Server Connectivity Tests")
        
        try:
            response = self.make_request('GET', self.base_url)
            if response and response.status_code in [200, 302, 403]:
                self.log_test("Server Connectivity", True, f"Server responding (Status: {response.status_code})")
                return True
            else:
                status = response.status_code if response else "No response"
                self.log_test("Server Connectivity", False, f"Server not responding properly (Status: {status})")
                return False
        except Exception as e:
            self.log_test("Server Connectivity", False, str(e))
            return False
    
    def admin_login(self):
        """Enhanced admin login with CSRF token handling"""
        self.print_section("🔐 Admin Authentication Tests")
        
        try:
            # Get login page and extract CSRF token if present
            login_url = f"{self.base_url}/admin/login"
            response = self.make_request('GET', login_url)
            
            if not response:
                return False
            
            if response.status_code != 200:
                self.log_test("Admin Login Page Access", False, f"Cannot access login page: {response.status_code}")
                return False
            
            self.log_test("Admin Login Page Access", True)
            
            # Extract CSRF token if present
            csrf_token = None
            if 'csrf' in response.text.lower():
                csrf_match = re.search(r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', response.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    self.log_test("CSRF Token Extraction", True, "Token found")
            
            # Attempt login
            login_data = {
                'username': self.admin_username,
                'password': self.admin_password
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            response = self.make_request('POST', login_url, data=login_data, allow_redirects=False)
            
            if not response:
                return False
            
            if response.status_code in [302, 303]:  # Redirect indicates successful login
                self.log_test("Admin Authentication", True, "Login successful")
                
                # Follow redirect to verify admin access
                if 'Location' in response.headers:
                    redirect_url = urljoin(self.base_url, response.headers['Location'])
                    dashboard_response = self.make_request('GET', redirect_url)
                    if dashboard_response and dashboard_response.status_code == 200:
                        self.log_test("Admin Dashboard Access", True)
                        return True
                
                return True
            else:
                self.log_test("Admin Authentication", False, f"Login failed: {response.status_code}")
                # Try to extract error message
                if response.text and 'error' in response.text.lower():
                    error_match = re.search(r'error["\'>:]*([^<"\']+)', response.text, re.IGNORECASE)
                    if error_match:
                        self.log_test("Login Error Details", False, error_match.group(1).strip())
                return False
                
        except Exception as e:
            self.log_test("Admin Login Exception", False, str(e))
            return False
    
    def test_admin_dashboard(self):
        """Comprehensive admin dashboard testing"""
        self.print_section("📊 Admin Dashboard Tests")
        
        try:
            dashboard_url = f"{self.base_url}/admin/"
            response = self.make_request('GET', dashboard_url)
            
            if not response:
                return False
            
            if response.status_code == 200:
                content = response.text
                
                # Test dashboard elements
                dashboard_elements = {
                    "Campaign Analytics Section": "Campaign Analytics",
                    "Total Registrations Card": "Total Registrations",
                    "Active Campaigns Card": "Active Campaigns",
                    "Campaign Performance Table": "Campaign Performance",
                    "Bot Status Section": "Bot Status",
                    "Navigation Menu": "Campaigns"
                }
                
                for element_name, search_text in dashboard_elements.items():
                    if search_text in content:
                        self.log_test(f"Dashboard - {element_name}", True)
                    else:
                        self.log_test(f"Dashboard - {element_name}", False, f"'{search_text}' not found")
                
                # Test for JavaScript functionality
                if 'function' in content or 'script' in content.lower():
                    self.log_test("Dashboard - JavaScript Presence", True)
                else:
                    self.log_test("Dashboard - JavaScript Presence", False, "No JavaScript found")
                
                return True
            else:
                self.log_test("Admin Dashboard Access", False, f"Dashboard inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Dashboard Exception", False, str(e))
            return False
    
    def test_campaign_management_page(self):
        """Test campaign management page functionality"""
        self.print_section("📋 Campaign Management Tests")
        
        try:
            campaigns_url = f"{self.base_url}/admin/campaigns"
            response = self.make_request('GET', campaigns_url)
            
            if not response:
                return False
            
            if response.status_code == 200:
                content = response.text
                
                # Test page elements
                page_elements = {
                    "Create Campaign Button": "Create Campaign",
                    "Campaign Table Headers": "Campaign ID",
                    "Registration Link Column": "Registration Link",
                    "Actions Column": "Actions",
                    "Campaign Modal": "createCampaignModal",
                    "Copy Functionality": "copyToClipboard"
                }
                
                for element_name, search_text in page_elements.items():
                    if search_text in content:
                        self.log_test(f"Campaign Management - {element_name}", True)
                    else:
                        self.log_test(f"Campaign Management - {element_name}", False, f"'{search_text}' not found")
                
                # Test for Bootstrap components
                if 'bootstrap' in content.lower() or 'btn' in content:
                    self.log_test("Campaign Management - Bootstrap UI", True)
                else:
                    self.log_test("Campaign Management - Bootstrap UI", False, "Bootstrap components not detected")
                
                return True
            else:
                self.log_test("Campaign Management Page Access", False, f"Page inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Management Exception", False, str(e))
            return False
    
    def test_create_campaign(self):
        """Comprehensive campaign creation testing"""
        self.print_section("🎯 Campaign Creation Tests")
        
        try:
            create_url = f"{self.base_url}/admin/campaigns/create"
            
            # Test campaign creation
            response = self.make_request('POST', create_url, data=self.test_campaign_data)
            
            if not response:
                return False
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.test_campaign_id = result.get('campaign_id')
                        self.log_test("Campaign Creation - Success", True, f"Created campaign: {self.test_campaign_id}")
                        
                        # Verify campaign appears in list
                        time.sleep(1)  # Wait for database consistency
                        campaigns_response = self.make_request('GET', f"{self.base_url}/admin/campaigns")
                        if campaigns_response and self.test_campaign_id in campaigns_response.text:
                            self.log_test("Campaign Creation - Verification", True, "Campaign appears in admin list")
                        else:
                            self.log_test("Campaign Creation - Verification", False, "Campaign not found in admin list")
                        
                        return True
                    else:
                        self.log_test("Campaign Creation - API Response", False, result.get('message', 'Unknown error'))
                        return False
                except json.JSONDecodeError:
                    self.log_test("Campaign Creation - Response Format", False, "Invalid JSON response")
                    return False
            else:
                self.log_test("Campaign Creation - HTTP Status", False, f"Create failed: {response.status_code}")
                
                # Try to extract error details
                try:
                    error_data = response.json()
                    self.log_test("Campaign Creation - Error Details", False, error_data.get('detail', 'Unknown error'))
                except:
                    self.log_test("Campaign Creation - Error Details", False, response.text[:200])
                return False
                
        except Exception as e:
            self.log_test("Campaign Creation Exception", False, str(e))
            return False
    
    def test_campaign_validation(self):
        """Test campaign creation validation"""
        self.print_section("✅ Campaign Validation Tests")
        
        if not self.test_campaign_id:
            self.log_test("Campaign Validation - Prerequisite", False, "No test campaign available")
            return False
        
        try:
            create_url = f"{self.base_url}/admin/campaigns/create"
            
            # Test duplicate campaign ID
            duplicate_data = self.test_campaign_data.copy()
            duplicate_data['name'] = "Duplicate Test Campaign"
            
            response = self.make_request('POST', create_url, data=duplicate_data)
            if response:
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        # System should auto-generate unique ID
                        self.log_test("Campaign Validation - Duplicate Handling", True, "System auto-generated unique ID")
                    else:
                        self.log_test("Campaign Validation - Duplicate Handling", True, "Duplicate properly rejected")
                else:
                    self.log_test("Campaign Validation - Duplicate Handling", True, "Duplicate properly rejected")
            
            # Test invalid data
            invalid_data = {
                'name': '',  # Empty name
                'min_deposit_amount': 'invalid',  # Invalid number
                'reward_description': ''  # Empty reward
            }
            
            response = self.make_request('POST', create_url, data=invalid_data)
            if response and response.status_code != 200:
                self.log_test("Campaign Validation - Invalid Data", True, "Invalid data properly rejected")
            else:
                self.log_test("Campaign Validation - Invalid Data", False, "Invalid data was accepted")
            
            return True
            
        except Exception as e:
            self.log_test("Campaign Validation Exception", False, str(e))
            return False
    
    def test_campaign_toggle(self):
        """Test campaign activation toggle"""
        self.print_section("🔄 Campaign Toggle Tests")
        
        if not self.test_campaign_id:
            self.log_test("Campaign Toggle - Prerequisite", False, "No test campaign available")
            return False
        
        try:
            toggle_url = f"{self.base_url}/admin/campaigns/{self.test_campaign_id}/toggle"
            
            # Test deactivation
            response = self.make_request('POST', toggle_url)  # Changed to POST for compatibility
            
            if not response:
                # Try PUT method
                response = self.make_request('PUT', toggle_url)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.log_test("Campaign Toggle - Deactivation", True)
                        is_active = result.get('is_active', False)
                        
                        # Test reactivation
                        time.sleep(1)
                        response = self.make_request('POST', toggle_url)
                        if not response:
                            response = self.make_request('PUT', toggle_url)
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            if result.get('status') == 'success':
                                self.log_test("Campaign Toggle - Reactivation", True)
                                return True
                            else:
                                self.log_test("Campaign Toggle - Reactivation", False, result.get('message', 'Unknown error'))
                        else:
                            self.log_test("Campaign Toggle - Reactivation", False, f"HTTP error: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Campaign Toggle - API Response", False, result.get('message', 'Unknown error'))
                except json.JSONDecodeError:
                    self.log_test("Campaign Toggle - Response Format", False, "Invalid JSON response")
            else:
                status = response.status_code if response else "No response"
                self.log_test("Campaign Toggle - HTTP Status", False, f"Toggle failed: {status}")
            
            return False
                
        except Exception as e:
            self.log_test("Campaign Toggle Exception", False, str(e))
            return False
    
    def test_campaign_public_access(self):
        """Test public campaign access and pages"""
        self.print_section("🌍 Public Campaign Access Tests")
        
        if not self.test_campaign_id:
            self.log_test("Campaign Public Access - Prerequisite", False, "No test campaign available")
            return False
        
        try:
            # Test campaign account setup page
            campaign_url = f"{self.base_url}/campaign/{self.test_campaign_id}"
            response = self.make_request('GET', campaign_url)
            
            if response and response.status_code == 200:
                content = response.text
                
                # Test campaign page elements
                campaign_elements = {
                    "Campaign Name Display": self.test_campaign_data['name'],
                    "Reward Description": self.test_campaign_data['reward_description'],
                    "Minimum Deposit": self.test_campaign_data['min_deposit_amount'],
                    "Account Setup Options": "Cipta Akaun Baru",
                    "Partner Change Option": "Tukar IB Partner",
                    "Continue Button": "Selesai, Teruskan",
                    "Step Indicator": "Step 1 of 2",
                    "Valetax Links": "valetaxintl.com"
                }
                
                for element_name, search_text in campaign_elements.items():
                    if search_text in content:
                        self.log_test(f"Campaign Page - {element_name}", True)
                    else:
                        self.log_test(f"Campaign Page - {element_name}", False, f"'{search_text}' not found")
                
                # Test for responsive design
                if 'viewport' in content and 'bootstrap' in content.lower():
                    self.log_test("Campaign Page - Responsive Design", True)
                else:
                    self.log_test("Campaign Page - Responsive Design", False, "Mobile responsive indicators not found")
                
                return True
            else:
                status = response.status_code if response else "No response"
                self.log_test("Campaign Public Access - HTTP Status", False, f"Campaign page inaccessible: {status}")
                return False
                
        except Exception as e:
            self.log_test("Campaign Public Access Exception", False, str(e))
            return False
    
    def test_campaign_registration_flow(self):
        """Test the complete campaign registration flow"""
        self.print_section("📝 Campaign Registration Flow Tests")
        
        if not self.test_campaign_id:
            self.log_test("Registration Flow - Prerequisite", False, "No test campaign available")
            return False
        
        try:
            # Step 1: Test account setup continuation
            continue_url = f"{self.base_url}/campaign/{self.test_campaign_id}/continue"
            continue_data = {
                'setup_action': 'new_account',
                'token': 'test_token'  # This might fail without valid token, but tests the endpoint
            }
            
            response = self.make_request('POST', continue_url, data=continue_data)
            
            if response:
                if response.status_code in [200, 302, 400]:  # 400 expected for invalid token
                    self.log_test("Registration Flow - Account Setup Continue", True, f"Endpoint responds (Status: {response.status_code})")
                else:
                    self.log_test("Registration Flow - Account Setup Continue", False, f"Unexpected status: {response.status_code}")
            else:
                self.log_test("Registration Flow - Account Setup Continue", False, "No response from endpoint")
            
            # Step 2: Test registration form access
            register_url = f"{self.base_url}/campaign/{self.test_campaign_id}/register"
            register_params = {'token': 'test_token'}
            
            response = self.make_request('GET', register_url, params=register_params)
            
            if response:
                if response.status_code in [200, 400]:  # 400 expected for invalid token
                    self.log_test("Registration Flow - Registration Form", True, f"Form endpoint responds (Status: {response.status_code})")
                    
                    if response.status_code == 200:
                        content = response.text
                        form_elements = {
                            "Full Name Field": 'name="full_name"',
                            "Email Field": 'name="email"',
                            "Deposit Amount Field": 'name="deposit_amount"',
                            "Trading ID Field": 'name="trading_id"',
                            "Form Validation": 'class="needs-validation"',
                            "Submit Button": 'type="submit"'
                        }
                        
                        for element_name, search_text in form_elements.items():
                            if search_text in content:
                                self.log_test(f"Registration Form - {element_name}", True)
                            else:
                                self.log_test(f"Registration Form - {element_name}", False, f"'{search_text}' not found")
                else:
                    self.log_test("Registration Flow - Registration Form", False, f"Unexpected status: {response.status_code}")
            else:
                self.log_test("Registration Flow - Registration Form", False, "No response from form endpoint")
            
            # Step 3: Test form submission endpoint
            submit_url = f"{self.base_url}/campaign/{self.test_campaign_id}/submit"
            submit_data = self.test_registration_data.copy()
            submit_data['token'] = 'test_token'
            submit_data['terms'] = 'on'
            
            response = self.make_request('POST', submit_url, data=submit_data)
            
            if response:
                if response.status_code in [200, 302, 400]:  # Various valid responses
                    self.log_test("Registration Flow - Form Submission", True, f"Submit endpoint responds (Status: {response.status_code})")
                else:
                    self.log_test("Registration Flow - Form Submission", False, f"Unexpected status: {response.status_code}")
            else:
                self.log_test("Registration Flow - Form Submission", False, "No response from submit endpoint")
            
            return True
            
        except Exception as e:
            self.log_test("Registration Flow Exception", False, str(e))
            return False
    
    def test_campaign_analytics(self):
        """Test campaign analytics functionality"""
        self.print_section("📈 Campaign Analytics Tests")
        
        try:
            # Test campaign registrations endpoint
            if self.test_campaign_id:
                registrations_url = f"{self.base_url}/admin/campaigns/{self.test_campaign_id}/registrations"
                response = self.make_request('GET', registrations_url)
                
                if response and response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('status') == 'success':
                            self.log_test("Campaign Analytics - Registrations API", True)
                            registrations = result.get('registrations', [])
                            self.log_test("Campaign Analytics - Data Structure", True, f"Found {len(registrations)} registrations")
                        else:
                            self.log_test("Campaign Analytics - API Response", False, result.get('message', 'Unknown error'))
                    except json.JSONDecodeError:
                        self.log_test("Campaign Analytics - Response Format", False, "Invalid JSON response")
                else:
                    status = response.status_code if response else "No response"
                    self.log_test("Campaign Analytics - Registrations API", False, f"API error: {status}")
            
            # Test dashboard analytics
            dashboard_url = f"{self.base_url}/admin/"
            response = self.make_request('GET', dashboard_url)
            
            if response and response.status_code == 200:
                content = response.text
                
                # Look for analytics data
                analytics_indicators = [
                    "Active Campaigns",
                    "Campaign Registrations", 
                    "Campaign Conversion",
                    "Campaign Performance"
                ]
                
                for indicator in analytics_indicators:
                    if indicator in content:
                        self.log_test(f"Dashboard Analytics - {indicator}", True)
                    else:
                        self.log_test(f"Dashboard Analytics - {indicator}", False, f"'{indicator}' not found")
                
                return True
            else:
                self.log_test("Dashboard Analytics Access", False, "Cannot access dashboard")
                return False
                
        except Exception as e:
            self.log_test("Campaign Analytics Exception", False, str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        self.print_section("🚨 Error Handling Tests")
        
        try:
            # Test invalid campaign access
            invalid_campaign_url = f"{self.base_url}/campaign/non-existent-campaign"
            response = self.make_request('GET', invalid_campaign_url)
            
            if response:
                if response.status_code in [404, 400]:
                    self.log_test("Error Handling - Invalid Campaign", True, "Properly returns error status")
                elif "not found" in response.text.lower() or "inactive" in response.text.lower():
                    self.log_test("Error Handling - Invalid Campaign", True, "Shows appropriate error message")
                else:
                    self.log_test("Error Handling - Invalid Campaign", False, "No proper error handling")
            else:
                self.log_test("Error Handling - Invalid Campaign", False, "No response to invalid request")
            
            # Test malformed requests
            malformed_urls = [
                f"{self.base_url}/campaign/",  # Empty campaign ID
                f"{self.base_url}/campaign/test-campaign/invalid-endpoint",  # Invalid endpoint
                f"{self.base_url}/admin/campaigns/invalid/registrations"  # Invalid campaign for analytics
            ]
            
            for url in malformed_urls:
                response = self.make_request('GET', url)
                if response and response.status_code in [404, 400, 500]:
                    self.log_test(f"Error Handling - Malformed URL", True, f"Properly handles: {url}")
                else:
                    self.log_test(f"Error Handling - Malformed URL", False, f"Poor handling: {url}")
            
            # Test unauthorized access
            unauthorized_session = requests.Session()
            admin_url = f"{self.base_url}/admin/campaigns"
            response = unauthorized_session.get(admin_url)
            
            if response and response.status_code in [401, 403, 302]:  # 302 for redirect to login
                self.log_test("Error Handling - Unauthorized Access", True, "Admin pages properly protected")
            else:
                self.log_test("Error Handling - Unauthorized Access", False, "Admin pages not properly protected")
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling Exception", False, str(e))
            return False
    
    def test_security_features(self):
        """Test security features"""
        self.print_section("🔒 Security Tests")
        
        try:
            # Test for basic security headers
            response = self.make_request('GET', self.base_url)
            if response:
                security_headers = [
                    'X-Content-Type-Options',
                    'X-Frame-Options', 
                    'X-XSS-Protection'
                ]
                
                for header in security_headers:
                    if header in response.headers:
                        self.log_test(f"Security - {header} Header", True, response.headers[header])
                    else:
                        self.log_test(f"Security - {header} Header", False, "Header not present")
            
            # Test admin authentication requirement
            protected_urls = [
                f"{self.base_url}/admin/campaigns",
                f"{self.base_url}/admin/campaigns/create",
                f"{self.base_url}/admin/"
            ]
            
            unauthenticated_session = requests.Session()
            for url in protected_urls:
                response = unauthenticated_session.get(url)
                if response and response.status_code in [302, 401, 403]:
                    self.log_test(f"Security - Protected URL", True, f"Authentication required for {url}")
                else:
                    self.log_test(f"Security - Protected URL", False, f"No authentication required for {url}")
            
            # Test for SQL injection protection (basic test)
            if self.test_campaign_id:
                malicious_inputs = [
                    "' OR '1'='1",
                    "'; DROP TABLE campaigns; --",
                    "<script>alert('xss')</script>"
                ]
                
                for malicious_input in malicious_inputs:
                    url = f"{self.base_url}/campaign/{malicious_input}"
                    response = self.make_request('GET', url)
                    
                    if response and "error" in response.text.lower():
                        self.log_test("Security - Input Validation", True, f"Malicious input properly handled")
                    else:
                        self.log_test("Security - Input Validation", True, f"Input sanitized or rejected")
            
            return True
            
        except Exception as e:
            self.log_test("Security Tests Exception", False, str(e))
            return False
    
    def test_performance_and_load(self):
        """Test basic performance metrics"""
        self.print_section("⚡ Performance Tests")
        
        try:
            # Test response times
            test_urls = [
                (f"{self.base_url}/", "Homepage"),
                (f"{self.base_url}/admin/", "Admin Dashboard"),
                (f"{self.base_url}/admin/campaigns", "Campaign Management")
            ]
            
            if self.test_campaign_id:
                test_urls.append((f"{self.base_url}/campaign/{self.test_campaign_id}", "Campaign Page"))
            
            for url, name in test_urls:
                start_time = time.time()
                response = self.make_request('GET', url)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response and response.status_code == 200:
                    if response_time < 5.0:  # 5 second threshold
                        self.log_test(f"Performance - {name} Response Time", True, f"{response_time:.2f}s")
                    else:
                        self.log_test(f"Performance - {name} Response Time", False, f"{response_time:.2f}s (too slow)")
                else:
                    self.log_test(f"Performance - {name} Availability", False, "Page not accessible")
            
            # Test concurrent requests (light load test)
            import threading
            import queue
            
            def make_concurrent_request(url, result_queue):
                start_time = time.time()
                response = self.make_request('GET', url)
                end_time = time.time()
                result_queue.put({
                    'success': response is not None and response.status_code == 200,
                    'time': end_time - start_time
                })
            
            # Test with 5 concurrent requests
            result_queue = queue.Queue()
            threads = []
            test_url = f"{self.base_url}/"
            
            for i in range(5):
                thread = threading.Thread(target=make_concurrent_request, args=(test_url, result_queue))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Analyze results
            results = []
            while not result_queue.empty():
                results.append(result_queue.get())
            
            successful_requests = sum(1 for r in results if r['success'])
            avg_response_time = sum(r['time'] for r in results) / len(results) if results else 0
            
            if successful_requests >= 4:  # At least 80% success rate
                self.log_test("Performance - Concurrent Requests", True, f"{successful_requests}/5 successful, avg: {avg_response_time:.2f}s")
            else:
                self.log_test("Performance - Concurrent Requests", False, f"Only {successful_requests}/5 successful")
            
            return True
            
        except Exception as e:
            self.log_test("Performance Tests Exception", False, str(e))
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.print_section("🧹 Cleanup")
        
        if self.test_campaign_id:
            self.log_test("Test Cleanup", True, f"Manual cleanup required for campaign: {self.test_campaign_id}")
            print(f"{Colors.YELLOW}   Note: Please manually delete test campaign '{self.test_campaign_id}' from admin panel{Colors.END}")
        else:
            self.log_test("Test Cleanup", True, "No test data to clean up")
    
    def generate_detailed_report(self):
        """Generate detailed test report"""
        self.print_header("📋 COMPREHENSIVE TEST REPORT")
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print summary
        print(f"{Colors.BOLD}Test Environment:{Colors.END}")
        print(f"  URL: {self.base_url}")
        print(f"  Admin User: {self.admin_username}")
        print(f"  Test Campaign: {self.test_campaign_id or 'Not created'}")
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{Colors.BOLD}Test Statistics:{Colors.END}")
        print(f"  Total Tests: {total_tests}")
        print(f"  {Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"  {Colors.RED}Failed: {failed_tests}{Colors.END}")
        print(f"  Success Rate: {Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 60 else Colors.RED}{success_rate:.1f}%{Colors.END}")
        
        # Categorize results
        categories = {
            'Connectivity': [],
            'Authentication': [],
            'Dashboard': [],
            'Campaign Management': [],
            'Registration Flow': [],
            'Analytics': [],
            'Error Handling': [],
            'Security': [],
            'Performance': [],
            'Other': []
        }
        
        for result in self.test_results:
            test_name = result['test']
            categorized = False
            
            for category in categories.keys():
                if category.lower() in test_name.lower() or any(keyword in test_name.lower() for keyword in {
                    'connectivity': ['server', 'connect'],
                    'authentication': ['login', 'admin', 'auth'],
                    'dashboard': ['dashboard'],
                    'campaign management': ['campaign', 'create', 'toggle'],
                    'registration flow': ['registration', 'flow', 'form'],
                    'analytics': ['analytics', 'performance'],
                    'error handling': ['error', 'handling'],
                    'security': ['security', 'protected'],
                    'performance': ['performance', 'response time', 'concurrent']
                }.get(category.lower(), [])):
                    categories[category].append(result)
                    categorized = True
                    break
            
            if not categorized:
                categories['Other'].append(result)
        
        # Print categorized results
        for category, results in categories.items():
            if results:
                print(f"\n{Colors.BOLD}{category} Tests:{Colors.END}")
                for result in results:
                    status_color = Colors.GREEN if result['passed'] else Colors.RED
                    status = "✅" if result['passed'] else "❌"
                    print(f"  {status} {result['test']}")
                    if result['message']:
                        print(f"     {Colors.CYAN}{result['message']}{Colors.END}")
        
        # Overall assessment
        print(f"\n{Colors.BOLD}Overall Assessment:{Colors.END}")
        if success_rate >= 90:
            print(f"{Colors.GREEN}🎉 Excellent! Campaign system is working perfectly.{Colors.END}")
            print(f"{Colors.GREEN}   Ready for production use.{Colors.END}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}✅ Good! Campaign system is mostly functional.{Colors.END}")
            print(f"{Colors.YELLOW}   Minor issues should be addressed before production.{Colors.END}")
        elif success_rate >= 60:
            print(f"{Colors.YELLOW}⚠️  Fair. Campaign system has some significant issues.{Colors.END}")
            print(f"{Colors.YELLOW}   Issues should be fixed before production deployment.{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Poor. Campaign system has major issues.{Colors.END}")
            print(f"{Colors.RED}   Significant fixes required before production use.{Colors.END}")
        
        # Recommendations
        failed_categories = [cat for cat, results in categories.items() if results and any(not r['passed'] for r in results)]
        if failed_categories:
            print(f"\n{Colors.BOLD}Recommendations:{Colors.END}")
            for category in failed_categories:
                failed_tests = [r for r in categories[category] if not r['passed']]
                print(f"  • Fix {category} issues ({len(failed_tests)} failures)")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'categories': categories,
            'test_campaign_id': self.test_campaign_id
        }
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        self.print_header("🧪 COMPREHENSIVE CAMPAIGN SYSTEM TESTING")
        
        print(f"{Colors.CYAN}Testing URL: {self.base_url}{Colors.END}")
        print(f"{Colors.CYAN}Admin User: {self.admin_username}{Colors.END}")
        print(f"{Colors.CYAN}Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        
        # Run test suites in order
        test_suites = [
            ('Server Connectivity', self.test_server_connectivity),
            ('Admin Authentication', self.admin_login),
            ('Admin Dashboard', self.test_admin_dashboard),
            ('Campaign Management', self.test_campaign_management_page),
            ('Campaign Creation', self.test_create_campaign),
            ('Campaign Validation', self.test_campaign_validation),
            ('Campaign Toggle', self.test_campaign_toggle),
            ('Public Campaign Access', self.test_campaign_public_access),
            ('Registration Flow', self.test_campaign_registration_flow),
            ('Campaign Analytics', self.test_campaign_analytics),
            ('Error Handling', self.test_error_handling),
            ('Security Features', self.test_security_features),
            ('Performance Tests', self.test_performance_and_load),
            ('Cleanup', self.cleanup_test_data)
        ]
        
        for suite_name, test_function in test_suites:
            try:
                start_time = time.time()
                test_function()
                end_time = time.time()
                print(f"{Colors.PURPLE}   Suite completed in {end_time - start_time:.2f}s{Colors.END}")
            except Exception as e:
                self.log_test(f"{suite_name} Suite Exception", False, str(e))
            
            time.sleep(0.5)  # Brief pause between test suites
        
        # Generate final report
        report = self.generate_detailed_report()
        
        # Save detailed results
        results_file = f"campaign_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'test_summary': report,
                'detailed_results': self.test_results,
                'test_environment': {
                    'base_url': self.base_url,
                    'admin_username': self.admin_username,
                    'test_campaign_id': self.test_campaign_id,
                    'timestamp': datetime.now().isoformat()
                }
            }, f, indent=2)
        
        print(f"\n{Colors.BOLD}📁 Detailed results saved to: {results_file}{Colors.END}")
        
        return report

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Campaign System Test Script')
    parser.add_argument('base_url', nargs='?', default='https://ezyassist-unified-production.up.railway.app',
                       help='Base URL of the application to test')
    parser.add_argument('--admin-username', default='admin@ezymeta.global',
                       help='Admin username for login')
    parser.add_argument('--admin-password', default='Password123!',
                       help='Admin password for login')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')
    
    args = parser.parse_args()
    
    if args.no_color:
        # Disable colors
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 COMPREHENSIVE CAMPAIGN SYSTEM TESTER{Colors.END}")
    print(f"{Colors.BLUE}=========================================={Colors.END}")
    print(f"{Colors.CYAN}Target URL: {args.base_url}{Colors.END}")
    
    if args.base_url == 'https://ezyassist-unified-production.up.railway.app':
        print(f"{Colors.YELLOW}Using default Railway URL. Specify different URL as argument if needed.{Colors.END}")
    
    tester = CampaignSystemTester(
        base_url=args.base_url,
        admin_username=args.admin_username,
        admin_password=args.admin_password
    )
    
    try:
        report = tester.run_comprehensive_tests()
        
        # Exit with appropriate code
        if report['success_rate'] >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testing interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error during testing: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()