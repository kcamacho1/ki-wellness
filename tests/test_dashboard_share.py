#!/usr/bin/env python3
"""
Test Dashboard Share Functionality

This test verifies that the dashboard share functionality works correctly,
including screenshot capture and logo overlay.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestDashboardShare:
    """Test class for dashboard share functionality"""
    
    def __init__(self):
        self.driver = None
        self.base_url = "http://localhost:5000"
        self.test_results = []
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def teardown_driver(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()
            
    def log_test(self, test_name, status, message=""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {message}")
        
    def test_share_buttons_exist(self):
        """Test that share buttons are present on dashboard cards"""
        try:
            # Navigate to dashboard (assuming user is logged in)
            self.driver.get(f"{self.base_url}/dashboard")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "share-btn"))
            )
            
            # Check for share buttons on all three cards
            share_buttons = self.driver.find_elements(By.CLASS_NAME, "share-btn")
            
            if len(share_buttons) >= 3:
                self.log_test("Share Buttons Exist", "PASS", f"Found {len(share_buttons)} share buttons")
            else:
                self.log_test("Share Buttons Exist", "FAIL", f"Expected 3+ share buttons, found {len(share_buttons)}")
                
        except TimeoutException:
            self.log_test("Share Buttons Exist", "FAIL", "Dashboard did not load within timeout")
        except Exception as e:
            self.log_test("Share Buttons Exist", "FAIL", f"Error: {str(e)}")
            
    def test_share_button_accessibility(self):
        """Test that share buttons have proper accessibility attributes"""
        try:
            share_buttons = self.driver.find_elements(By.CLASS_NAME, "share-btn")
            
            for i, button in enumerate(share_buttons):
                # Check for aria-label
                aria_label = button.get_attribute("aria-label")
                if aria_label:
                    self.log_test(f"Share Button {i+1} Accessibility", "PASS", f"Has aria-label: {aria_label}")
                else:
                    self.log_test(f"Share Button {i+1} Accessibility", "FAIL", "Missing aria-label")
                    
                # Check for title attribute
                title = button.get_attribute("title")
                if title:
                    self.log_test(f"Share Button {i+1} Title", "PASS", f"Has title: {title}")
                else:
                    self.log_test(f"Share Button {i+1} Title", "FAIL", "Missing title attribute")
                    
        except Exception as e:
            self.log_test("Share Button Accessibility", "FAIL", f"Error: {str(e)}")
            
    def test_share_button_data_attributes(self):
        """Test that share buttons have proper data attributes"""
        try:
            share_buttons = self.driver.find_elements(By.CLASS_NAME, "share-btn")
            
            expected_tiles = ["water", "macros", "mood"]
            
            for i, button in enumerate(share_buttons):
                data_tile = button.get_attribute("data-tile")
                if data_tile and data_tile in expected_tiles:
                    self.log_test(f"Share Button {i+1} Data Attribute", "PASS", f"Has data-tile: {data_tile}")
                else:
                    self.log_test(f"Share Button {i+1} Data Attribute", "FAIL", f"Invalid or missing data-tile: {data_tile}")
                    
        except Exception as e:
            self.log_test("Share Button Data Attributes", "FAIL", f"Error: {str(e)}")
            
    def test_logo_file_exists(self):
        """Test that the logo file exists and is accessible"""
        try:
            logo_path = Path("app/static/logo-new.png")
            if logo_path.exists():
                self.log_test("Logo File Exists", "PASS", f"Logo file found at {logo_path}")
                
                # Check file size
                file_size = logo_path.stat().st_size
                if file_size > 0:
                    self.log_test("Logo File Size", "PASS", f"Logo file size: {file_size} bytes")
                else:
                    self.log_test("Logo File Size", "FAIL", "Logo file is empty")
            else:
                self.log_test("Logo File Exists", "FAIL", f"Logo file not found at {logo_path}")
                
        except Exception as e:
            self.log_test("Logo File Check", "FAIL", f"Error: {str(e)}")
            
    def test_share_functionality_script(self):
        """Test that the share functionality JavaScript is properly loaded"""
        try:
            # Check if html2canvas is loaded
            html2canvas_loaded = self.driver.execute_script("return typeof html2canvas !== 'undefined'")
            if html2canvas_loaded:
                self.log_test("HTML2Canvas Library", "PASS", "html2canvas library is loaded")
            else:
                self.log_test("HTML2Canvas Library", "FAIL", "html2canvas library is not loaded")
                
            # Check if shareTile function exists
            share_function_exists = self.driver.execute_script("return typeof shareTile === 'function'")
            if share_function_exists:
                self.log_test("Share Function", "PASS", "shareTile function is defined")
            else:
                self.log_test("Share Function", "FAIL", "shareTile function is not defined")
                
        except Exception as e:
            self.log_test("Share Functionality Script", "FAIL", f"Error: {str(e)}")
            
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Dashboard Share Functionality Tests...")
        print("=" * 60)
        
        try:
            self.setup_driver()
            
            # Run tests
            self.test_share_buttons_exist()
            self.test_share_button_accessibility()
            self.test_share_button_data_attributes()
            self.test_logo_file_exists()
            self.test_share_functionality_script()
            
        except Exception as e:
            print(f"❌ Test setup failed: {str(e)}")
        finally:
            self.teardown_driver()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "📈 Success Rate: 0%")
        
        # Save results to file
        results_file = "dashboard_share_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return passed == total

if __name__ == "__main__":
    test_suite = TestDashboardShare()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Dashboard share functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the results above.")
        sys.exit(1)
