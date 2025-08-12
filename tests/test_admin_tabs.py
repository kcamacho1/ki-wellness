#!/usr/bin/env python3
"""
Test script to verify admin dashboard tabs functionality
"""

import sys
import os
# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

def test_admin_dashboard_tabs():
    """Test that all admin dashboard tabs are accessible"""
    print("🔍 Testing Admin Dashboard Tabs...")
    
    try:
        with app.test_client() as client:
            # Test admin dashboard route
            response = client.get('/admin')
            print(f"✅ Admin dashboard status: {response.status_code}")
            
            if response.status_code == 302:
                print("ℹ️  Admin dashboard redirects (authentication required)")
            elif response.status_code == 200:
                print("✅ Admin dashboard loads successfully")
                
                # Check if all tab content divs are present in the HTML
                html_content = response.get_data(as_text=True)
                
                # Check for all required tab content divs
                required_tabs = [
                    'overview-tab',
                    'users-tab', 
                    'content-tab',
                    'analytics-tab',
                    'financial-tab',
                    'ai-costs-tab',
                    'system-tab'
                ]
                
                missing_tabs = []
                for tab in required_tabs:
                    if f'id="{tab}"' not in html_content:
                        missing_tabs.append(tab)
                
                if missing_tabs:
                    print(f"❌ Missing tab content divs: {missing_tabs}")
                    return False
                else:
                    print("✅ All tab content divs are present")
                
                # Check for tab buttons
                required_buttons = [
                    'data-tab="overview"',
                    'data-tab="users"',
                    'data-tab="content"',
                    'data-tab="analytics"',
                    'data-tab="financial"',
                    'data-tab="ai-costs"',
                    'data-tab="system"'
                ]
                
                missing_buttons = []
                for button in required_buttons:
                    if button not in html_content:
                        missing_buttons.append(button)
                
                if missing_buttons:
                    print(f"❌ Missing tab buttons: {missing_buttons}")
                    return False
                else:
                    print("✅ All tab buttons are present")
                
                # Check for showTab function
                if 'function showTab(' not in html_content:
                    print("❌ showTab function is missing")
                    return False
                else:
                    print("✅ showTab function is present")
                
                # Check for proper tab initialization
                if 'showTab(\'overview\')' not in html_content:
                    print("❌ Tab initialization is missing")
                    return False
                else:
                    print("✅ Tab initialization is present")
                
                return True
            else:
                print(f"❌ Admin dashboard returned unexpected status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing admin dashboard: {e}")
        return False

def main():
    """Run the test"""
    print("🚀 Testing Admin Dashboard Tab Functionality\n")
    
    success = test_admin_dashboard_tabs()
    
    if success:
        print("\n🎉 All admin dashboard tabs are working correctly!")
        print("✅ Tab structure is properly organized")
        print("✅ All tab content divs are present")
        print("✅ All tab buttons are configured")
        print("✅ JavaScript functionality is in place")
        return True
    else:
        print("\n⚠️  Some issues found with admin dashboard tabs")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
