#!/usr/bin/env python3
"""
Script to help refactor app.py by removing duplicate admin routes
"""

import re

def find_admin_routes_in_app():
    """Find all admin routes in app.py that should be removed"""
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Find all admin routes
    admin_route_pattern = r'@app\.route\([\'\"]/api/admin/.*?\n.*?def.*?\(.*?\):.*?(?=@app\.route|^[^\s]|\Z)'
    admin_routes = re.findall(admin_route_pattern, content, re.DOTALL | re.MULTILINE)
    
    print(f"Found {len(admin_routes)} admin routes to remove:")
    for i, route in enumerate(admin_routes):
        lines = route.split('\n')
        print(f"{i+1}. {lines[0]}")
        if len(lines) > 1:
            print(f"   Function: {lines[1].strip()}")
    
    return admin_routes

def remove_admin_routes():
    """Remove duplicate admin routes from app.py"""
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    # List of admin route paths that are already in admin blueprint
    admin_routes_to_remove = [
        '/api/admin/settings',
        '/api/admin/analytics', 
        '/api/admin/ai-usage',
        '/api/admin/revenue',
        '/api/admin/assign-ff-roles',
        '/api/admin/users',
        '/api/admin/update-user-role',
        '/api/admin/security-stats',
        '/api/admin/unblock-ip'
    ]
    
    # Remove each admin route and its function
    for route_path in admin_routes_to_remove:
        # Pattern to match the route decorator and entire function
        pattern = rf'@app\.route\([\'\"]{re.escape(route_path)}[\'\"](.*?)\n.*?def.*?\(.*?\):.*?(?=\n@|\n[^\s]|\Z)'
        content = re.sub(pattern, f'# Admin route {route_path} moved to routes/admin.py\n', content, flags=re.DOTALL)
    
    # Write back to file
    with open('app.py', 'w') as f:
        f.write(content)
    
    print("Removed duplicate admin routes from app.py")

if __name__ == '__main__':
    print("Analyzing admin routes in app.py...")
    find_admin_routes_in_app()
    print("\nRemoving duplicate admin routes...")
    remove_admin_routes()
    print("Done!")
