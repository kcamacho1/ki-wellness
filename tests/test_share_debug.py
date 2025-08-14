#!/usr/bin/env python3
"""
Debug script to test share functionality and identify blank card issue
"""

import os
import sys
from pathlib import Path

def check_dashboard_structure():
    """Check the dashboard HTML structure for potential issues"""
    print("🔍 Checking Dashboard Structure")
    print("=" * 50)
    
    dashboard_path = Path("app/templates/dashboard.html")
    
    if not dashboard_path.exists():
        print("❌ Dashboard template not found")
        return False
    
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Check for card containers
    if 'data-tile="water"' in content:
        print("✅ Water tile found")
    else:
        print("❌ Water tile missing")
        return False
    
    if 'data-tile="macros"' in content:
        print("✅ Macros tile found")
    else:
        print("❌ Macros tile missing")
        return False
    
    if 'data-tile="mood"' in content:
        print("✅ Mood tile found")
    else:
        print("❌ Mood tile missing")
        return False
    
    # Check for data elements
    data_elements = [
        'id="waterAmount"',
        'id="totalCalories"',
        'id="moodEmoji"',
        'id="moodText"'
    ]
    
    for element in data_elements:
        if element in content:
            print(f"✅ {element} found")
        else:
            print(f"❌ {element} missing")
            return False
    
    return True

def check_share_implementation():
    """Check the share implementation for potential issues"""
    print("\n🔍 Checking Share Implementation")
    print("=" * 50)
    
    js_path = Path("app/static/js/dashboard_module.js")
    
    if not js_path.exists():
        print("❌ Dashboard module not found")
        return False
    
    with open(js_path, 'r') as f:
        content = f.read()
    
    # Check for potential issues
    issues = []
    
    # Check if html2canvas is properly configured
    if 'removeContainer: false' in content:
        print("✅ removeContainer set to false (good)")
    else:
        print("⚠️  removeContainer might be true (could cause issues)")
        issues.append("removeContainer")
    
    # Check for proper element selection
    if '.closest(\'.bg-white\')' in content:
        print("✅ Proper element selection found")
    else:
        print("❌ Element selection might be incorrect")
        issues.append("element selection")
    
    # Check for debugging
    if 'logging: true' in content:
        print("✅ Debug logging enabled")
    else:
        print("⚠️  Debug logging disabled")
    
    # Check for proper error handling
    if 'console.error' in content and 'Error sharing tile' in content:
        print("✅ Error handling found")
    else:
        print("❌ Error handling missing")
        issues.append("error handling")
    
    return len(issues) == 0

def check_css_potential_issues():
    """Check for CSS issues that might cause blank captures"""
    print("\n🔍 Checking CSS Potential Issues")
    print("=" * 50)
    
    dashboard_path = Path("app/templates/dashboard.html")
    
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Check for opacity issues
    if 'opacity-0' in content:
        print("⚠️  opacity-0 found (might cause blank captures)")
    else:
        print("✅ No opacity-0 found")
    
    # Check for visibility issues
    if 'hidden' in content:
        print("⚠️  'hidden' class found (might cause blank captures)")
    else:
        print("✅ No 'hidden' class found")
    
    # Check for display issues
    if 'display: none' in content:
        print("⚠️  'display: none' found (might cause blank captures)")
    else:
        print("✅ No 'display: none' found")
    
    return True

def suggest_fixes():
    """Suggest fixes for the blank card issue"""
    print("\n🔧 Suggested Fixes")
    print("=" * 50)
    
    print("1. Ensure html2canvas configuration:")
    print("   - Set removeContainer: false")
    print("   - Enable logging: true for debugging")
    print("   - Add proper element visibility checks")
    
    print("\n2. Add element preparation before capture:")
    print("   - Set display: block")
    print("   - Set visibility: visible")
    print("   - Set opacity: 1")
    print("   - Wait for animations to complete")
    
    print("\n3. Check for CSS conflicts:")
    print("   - Ensure no opacity-0 on target elements")
    print("   - Ensure no hidden or display: none")
    print("   - Check for transform issues")
    
    print("\n4. Add debugging:")
    print("   - Log canvas dimensions")
    print("   - Log element properties before capture")
    print("   - Check if element is visible")

def main():
    """Run debug checks"""
    print("🚀 Share Functionality Debug")
    print("=" * 60)
    
    # Run checks
    structure_ok = check_dashboard_structure()
    implementation_ok = check_share_implementation()
    css_ok = check_css_potential_issues()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    
    if structure_ok:
        print("✅ Dashboard Structure: OK")
    else:
        print("❌ Dashboard Structure: ISSUES FOUND")
    
    if implementation_ok:
        print("✅ Share Implementation: OK")
    else:
        print("❌ Share Implementation: ISSUES FOUND")
    
    if css_ok:
        print("✅ CSS Analysis: OK")
    else:
        print("❌ CSS Analysis: ISSUES FOUND")
    
    # Suggest fixes
    suggest_fixes()
    
    print("\n💡 Next Steps:")
    print("1. Test the share functionality in browser")
    print("2. Check browser console for errors")
    print("3. Verify html2canvas is loading properly")
    print("4. Ensure all data elements have content")

if __name__ == "__main__":
    main()
