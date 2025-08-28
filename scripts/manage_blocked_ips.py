#!/usr/bin/env python3
"""
Script to manage blocked IPs in the security middleware
Usage: python manage_blocked_ips.py [list|unblock] [ip_address]
"""

import sys
import os

# Add the parent directory to the path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, security_middleware

def list_blocked_ips():
    """List all currently blocked IPs"""
    with security_middleware.lock:
        blocked_ips = security_middleware.bot_signatures['blocked_ips']
        if blocked_ips:
            print("🚫 Currently blocked IPs:")
            for ip in blocked_ips:
                print(f"  - {ip}")
        else:
            print("✅ No IPs are currently blocked")

def unblock_ip(ip_address):
    """Unblock a specific IP address"""
    if not ip_address:
        print("❌ Please provide an IP address to unblock")
        return
    
    security_middleware.unblock_ip(ip_address)
    print(f"✅ IP {ip_address} has been unblocked")

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_blocked_ips.py [list|unblock] [ip_address]")
        print("Examples:")
        print("  python manage_blocked_ips.py list")
        print("  python manage_blocked_ips.py unblock 192.168.1.100")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_blocked_ips()
    elif command == "unblock":
        ip_address = sys.argv[2] if len(sys.argv) > 2 else None
        unblock_ip(ip_address)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, unblock")
        sys.exit(1)

if __name__ == "__main__":
    main()
