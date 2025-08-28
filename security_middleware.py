import re
import time
from functools import wraps
from flask import request, jsonify, current_app, g
from datetime import datetime, timedelta
import threading

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.rate_limit_db = {}
        self.bot_signatures = {
            'bot_headers': [
                'bot', 'crawler', 'spider', 'scraper', 'python', 'curl', 'wget',
                'http', 'java', 'perl', 'ruby', 'php', 'go', 'rust'
            ],
            'suspicious_ips': set(),
            'blocked_ips': set()
        }
        self.lock = threading.Lock()
        
        # Check if we're in development mode for CSP relaxation
        self.is_development = (
            app.debug or 
            app.config.get('ENV') == 'development' or
            app.config.get('FLASK_ENV') == 'development' or
            not app.config.get('DATABASE_URL', '').startswith('postgresql')
        )
        
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
    def before_request(self):
        """Security checks before each request"""
        g.request_start_time = time.time()
        
        # Allow homepage access with more relaxed security
        if request.endpoint in ['index', 'landing'] or request.path == '/':
            # Only apply rate limiting and input validation for homepage
            if not self.check_rate_limit(request.remote_addr):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            if not self.validate_inputs(request):
                return jsonify({'error': 'Invalid input detected'}), 400
            return  # Skip bot detection for homepage
        
        # Check if IP is blocked
        if self.is_ip_blocked(request.remote_addr):
            print(f"🚫 Blocked IP attempted access: {request.remote_addr} for {request.path}")
            return jsonify({'error': 'Access denied'}), 403
            
        # Bot detection (skip for homepage)
        if self.detect_bot(request):
            print(f"🤖 Bot detected and blocked: IP={request.remote_addr}, UA={request.headers.get('User-Agent', 'None')}, Path={request.path}")
            self.block_ip(request.remote_addr)
            return jsonify({'error': 'Bot access denied'}), 403
            
        # Rate limiting
        if not self.check_rate_limit(request.remote_addr):
            return jsonify({'error': 'Rate limit exceeded'}), 429
            
        # Input validation
        if not self.validate_inputs(request):
            return jsonify({'error': 'Invalid input detected'}), 400
            
    def after_request(self, response):
        """Add security headers after each request"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Updated CSP to allow necessary external resources
        if self.is_development:
            # More relaxed CSP for development
            csp = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:",
                "style-src 'self' 'unsafe-inline' https:",
                "font-src 'self' https:",
                "img-src 'self' data: https:",
                "connect-src 'self' https:",
                "frame-src https:",
                "object-src 'none'",
                "base-uri 'self'"
            ]
        else:
            # Strict CSP for production (but Alpine.js needs 'unsafe-eval')
            csp = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.google.com https://www.gstatic.com https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://unpkg.com",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com",
                "font-src 'self' https://fonts.gstatic.com",
                "img-src 'self' data: https:",
                "connect-src 'self' https://www.google.com https://www.gstatic.com",
                "frame-src https://www.google.com",
                "object-src 'none'",
                "base-uri 'self'"
            ]
        response.headers['Content-Security-Policy'] = "; ".join(csp)
        
        # Remove server information
        response.headers.pop('Server', None)
        
        return response
        
    def is_ip_blocked(self, ip):
        """Check if IP is blocked"""
        with self.lock:
            return ip in self.bot_signatures['blocked_ips']
            
    def block_ip(self, ip):
        """Block an IP address"""
        with self.lock:
            self.bot_signatures['blocked_ips'].add(ip)
            
    def unblock_ip(self, ip):
        """Unblock an IP address"""
        with self.lock:
            self.bot_signatures['blocked_ips'].discard(ip)
            
    def detect_bot(self, request):
        """Detect bot-like behavior"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # Only block obvious bots/crawlers, not legitimate browsers
        obvious_bot_signatures = [
            'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider',
            'yandexbot', 'facebookexternalhit', 'twitterbot', 'linkedinbot',
            'whatsapp', 'telegrambot', 'wget', 'curl', 'postman', 'python-requests',
            'scrapy', 'crawler', 'spider', 'scraper'
        ]
        
        # Check for obvious bot signatures in User-Agent
        for signature in obvious_bot_signatures:
            if signature in user_agent:
                return True
        
        # Only flag as bot if User-Agent is completely missing or suspiciously minimal
        if not user_agent or len(user_agent.strip()) < 10:
            return True
            
        # Check for automated request patterns (more permissive)
        if self.detect_automated_patterns(request):
            return True
            
        return False
        
    def detect_automated_patterns(self, request):
        """Detect automated request patterns"""
        # Check request frequency
        current_time = time.time()
        ip = request.remote_addr
        
        with self.lock:
            if ip not in self.rate_limit_db:
                self.rate_limit_db[ip] = {'requests': [], 'last_request': current_time}
                
            ip_data = self.rate_limit_db[ip]
            ip_data['requests'].append(current_time)
            
            # Keep only last 60 seconds of requests
            ip_data['requests'] = [req_time for req_time in ip_data['requests'] 
                                 if current_time - req_time < 60]
            
            # Check for extremely suspicious patterns only
            if len(ip_data['requests']) > 200:  # More than 200 requests per minute (very aggressive)
                return True
                
            # Check for requests that are extremely regular (clearly automated)
            if len(ip_data['requests']) > 20:  # Require more requests to analyze patterns
                intervals = [ip_data['requests'][i] - ip_data['requests'][i-1] 
                           for i in range(1, len(ip_data['requests']))]
                # Only flag if intervals are extremely regular (within 50ms)
                if len(intervals) > 5 and all(abs(interval - intervals[0]) < 0.05 for interval in intervals):
                    return True  # Extremely regular intervals suggest clear automation
                    
        return False
        
    def check_rate_limit(self, ip):
        """Check rate limiting for an IP"""
        current_time = time.time()
        
        with self.lock:
            if ip not in self.rate_limit_db:
                self.rate_limit_db[ip] = {'requests': [], 'last_request': current_time}
                
            ip_data = self.rate_limit_db[ip]
            
            # Clean old requests (older than 1 minute)
            ip_data['requests'] = [req_time for req_time in ip_data['requests'] 
                                 if current_time - req_time < 60]
            
            # Check rate limit (max 60 requests per minute)
            if len(ip_data['requests']) >= 60:
                return False
                
            ip_data['requests'].append(current_time)
            ip_data['last_request'] = current_time
            
        return True
        
    def validate_inputs(self, request):
        """Validate and sanitize user inputs"""
        # Check for SQL injection patterns
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b)',
            r'(\b(and|or)\s+\d+\s*[=<>])',
            r'(\b(union|select).*from)',
            r'(\b(insert|update|delete).*where)',
            r'(\b(drop|create|alter).*table)',
            r'(\b(exec|execute).*xp_)',
            r'(\b(script|javascript|vbscript|onload|onerror))',
            r'(\b(union|select).*information_schema)',
            r'(\b(union|select).*sys\.)',
            r'(\b(union|select).*mysql\.)'
        ]
        
        # Check all request data
        request_data = {
            'args': dict(request.args),
            'form': dict(request.form),
            'json': request.get_json() if request.is_json else {},
            'headers': dict(request.headers)
        }
        
        for data_type, data in request_data.items():
            if not self._check_data_for_sql_injection(data, sql_patterns):
                return False
                
        return True
        
    def _check_data_for_sql_injection(self, data, patterns):
        """Check data for SQL injection patterns"""
        if isinstance(data, dict):
            for key, value in data.items():
                if not self._check_data_for_sql_injection(key, patterns):
                    return False
                if not self._check_data_for_sql_injection(value, patterns):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self._check_data_for_sql_injection(item, patterns):
                    return False
        elif isinstance(data, str):
            data_lower = data.lower()
            for pattern in patterns:
                if re.search(pattern, data_lower, re.IGNORECASE):
                    print(f"🚨 SQL Injection attempt detected: {data}")
                    return False
                    
        return True

# Rate limiting decorator
def rate_limit(max_requests=60, window=60):
    """Rate limiting decorator for specific endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            current_time = time.time()
            
            # Simple in-memory rate limiting
            if not hasattr(g, 'rate_limit_data'):
                g.rate_limit_data = {}
                
            if ip not in g.rate_limit_data:
                g.rate_limit_data[ip] = {'requests': [], 'last_request': current_time}
                
            ip_data = g.rate_limit_data[ip]
            
            # Clean old requests
            ip_data['requests'] = [req_time for req_time in ip_data['requests'] 
                                 if current_time - req_time < window]
            
            # Check rate limit
            if len(ip_data['requests']) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
                
            ip_data['requests'].append(current_time)
            ip_data['last_request'] = current_time
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Input sanitization function
def sanitize_input(input_data):
    """Sanitize user input to prevent XSS and injection attacks"""
    if isinstance(input_data, str):
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
        for char in dangerous_chars:
            input_data = input_data.replace(char, '')
        return input_data.strip()
    elif isinstance(input_data, dict):
        return {key: sanitize_input(value) for key, value in input_data.items()}
    elif isinstance(input_data, list):
        return [sanitize_input(item) for item in input_data]
    else:
        return input_data

# Note: CSRF protection is now handled by reCAPTCHA v2 on sensitive forms
