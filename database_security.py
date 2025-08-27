import re
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class DatabaseSecurity:
    """Database security utilities to prevent SQL injection attacks"""
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        # Basic SQL commands
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
        # SQL operators with numbers
        r'\b(and|or)\s+\d+\s*[=<>]',
        # SQL with FROM clause
        r'\b(union|select).*from',
        # SQL with WHERE clause
        r'\b(insert|update|delete).*where',
        # Table operations
        r'\b(drop|create|alter).*table',
        # Extended procedures
        r'\b(exec|execute).*xp_',
        # System tables
        r'\b(union|select).*information_schema',
        r'\b(union|select).*sys\.',
        r'\b(union|select).*mysql\.',
        # Comment syntax
        r'--',
        r'/\*.*\*/',
        # Batch commands
        r';\s*(select|insert|update|delete|drop|create|alter)',
        # Hex encoded
        r'0x[0-9a-fA-F]+',
        # URL encoded
        r'%27|%22|%3C|%3E',
        # Unicode encoded
        r'\\u[0-9a-fA-F]{4}',
        # Null byte
        r'\x00',
        # Stacked queries
        r';\s*exec\s*\(',
        r';\s*execute\s*\(',
        # Time-based attacks
        r'waitfor\s+delay',
        r'benchmark\s*\(',
        r'sleep\s*\(',
        # Boolean-based attacks
        r'and\s+1=1',
        r'or\s+1=1',
        r'and\s+true',
        r'or\s+true'
    ]
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
        r'<select[^>]*>.*?</select>',
        r'<button[^>]*>.*?</button>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<link[^>]*>',
        r'<base[^>]*>',
        r'<bgsound[^>]*>',
        r'<applet[^>]*>.*?</applet>',
        r'<marquee[^>]*>.*?</marquee>',
        r'<xmp[^>]*>.*?</xmp>',
        r'<plaintext[^>]*>.*?</plaintext>',
        r'<listing[^>]*>.*?</listing>',
        # Event handlers
        r'on\w+\s*=',
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'vbscript:',
        # CSS expressions
        r'expression\s*\(',
        r'url\s*\(',
        r'import\s*\(',
        # PHP code
        r'<\?php',
        r'<\?=',
        r'<\?',
        # ASP code
        r'<%',
        r'<%=',
        r'<%\s*response\.',
        # JSP code
        r'<%\s*@\s*page',
        r'<%\s*@\s*include',
        r'<%\s*@\s*taglib'
    ]
    
    @classmethod
    def validate_input(cls, input_data: Any, max_length: Optional[int] = None) -> bool:
        """
        Validate input data for security threats
        
        Args:
            input_data: The input data to validate
            max_length: Maximum allowed length for strings
            
        Returns:
            True if input is safe, False otherwise
        """
        try:
            if isinstance(input_data, str):
                return cls._validate_string(input_data, max_length)
            elif isinstance(input_data, dict):
                return cls._validate_dict(input_data, max_length)
            elif isinstance(input_data, list):
                return cls._validate_list(input_data, max_length)
            elif input_data is None:
                return True
            else:
                # For other types, convert to string and validate
                return cls._validate_string(str(input_data), max_length)
        except Exception as e:
            print(f"❌ Input validation error: {e}")
            return False
    
    @classmethod
    def _validate_string(cls, input_string: str, max_length: Optional[int] = None) -> bool:
        """Validate a string input"""
        if not isinstance(input_string, str):
            return False
            
        # Check length
        if max_length and len(input_string) > max_length:
            print(f"🚨 Input too long: {len(input_string)} > {max_length}")
            return False
            
        # Check for SQL injection
        if cls._contains_sql_injection(input_string):
            return False
            
        # Check for XSS
        if cls._contains_xss(input_string):
            return False
            
        # Check for null bytes
        if '\x00' in input_string:
            print("🚨 Null byte detected in input")
            return False
            
        return True
    
    @classmethod
    def _validate_dict(cls, input_dict: Dict, max_length: Optional[int] = None) -> bool:
        """Validate a dictionary input"""
        if not isinstance(input_dict, dict):
            return False
            
        for key, value in input_dict.items():
            if not cls._validate_string(str(key), max_length):
                return False
            if not cls.validate_input(value, max_length):
                return False
                
        return True
    
    @classmethod
    def _validate_list(cls, input_list: List, max_length: Optional[int] = None) -> bool:
        """Validate a list input"""
        if not isinstance(input_list, list):
            return False
            
        for item in input_list:
            if not cls.validate_input(item, max_length):
                return False
                
        return True
    
    @classmethod
    def _contains_sql_injection(cls, input_string: str) -> bool:
        """Check if string contains SQL injection patterns"""
        input_lower = input_string.lower()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                print(f"🚨 SQL Injection pattern detected: {pattern}")
                return True
                
        return False
    
    @classmethod
    def _contains_xss(cls, input_string: str) -> bool:
        """Check if string contains XSS patterns"""
        input_lower = input_string.lower()
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                print(f"🚨 XSS pattern detected: {pattern}")
                return True
                
        return False
    
    @classmethod
    def sanitize_input(cls, input_data: Any, max_length: Optional[int] = None) -> Any:
        """
        Sanitize input data by removing dangerous characters
        
        Args:
            input_data: The input data to sanitize
            max_length: Maximum allowed length for strings
            
        Returns:
            Sanitized input data
        """
        try:
            if isinstance(input_data, str):
                return cls._sanitize_string(input_data, max_length)
            elif isinstance(input_data, dict):
                return cls._sanitize_dict(input_data, max_length)
            elif isinstance(input_data, list):
                return cls._sanitize_list(input_data, max_length)
            else:
                return input_data
        except Exception as e:
            print(f"❌ Input sanitization error: {e}")
            return None
    
    @classmethod
    def _sanitize_string(cls, input_string: str, max_length: Optional[int] = None) -> str:
        """Sanitize a string input"""
        if not isinstance(input_string, str):
            return ""
            
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']', '\x00']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
            
        # Remove extra whitespace
        sanitized = ' '.join(sanitized.split())
        
        # Truncate if too long
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized
    
    @classmethod
    def _sanitize_dict(cls, input_dict: Dict, max_length: Optional[int] = None) -> Dict:
        """Sanitize a dictionary input"""
        if not isinstance(input_dict, dict):
            return {}
            
        sanitized = {}
        for key, value in input_dict.items():
            sanitized_key = cls._sanitize_string(str(key), max_length)
            sanitized_value = cls.sanitize_input(value, max_length)
            if sanitized_key and sanitized_value is not None:
                sanitized[sanitized_key] = sanitized_value
                
        return sanitized
    
    @classmethod
    def _sanitize_list(cls, input_list: List, max_length: Optional[int] = None) -> List:
        """Sanitize a list input"""
        if not isinstance(input_list, list):
            return []
            
        sanitized = []
        for item in input_list:
            sanitized_item = cls.sanitize_input(item, max_length)
            if sanitized_item is not None:
                sanitized.append(sanitized_item)
                
        return sanitized
    
    @classmethod
    def safe_query(cls, query_string: str, params: Optional[Dict] = None) -> str:
        """
        Create a safe SQL query using parameterized queries
        
        Args:
            query_string: The SQL query string
            params: Parameters for the query
            
        Returns:
            Safe query string
        """
        try:
            # Validate the query string
            if not cls._validate_string(query_string):
                raise ValueError("Query string contains unsafe patterns")
                
            # If using SQLAlchemy, use text() for safe parameterization
            if params:
                # Validate parameters
                for key, value in params.items():
                    if not cls.validate_input(value):
                        raise ValueError(f"Parameter {key} contains unsafe data")
                        
                # Create parameterized query
                safe_query = text(query_string)
                return safe_query
            else:
                return query_string
                
        except Exception as e:
            print(f"❌ Query validation error: {e}")
            raise
    
    @classmethod
    def log_security_event(cls, event_type: str, details: str, ip_address: str = None):
        """Log security events for monitoring"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] SECURITY: {event_type} - {details}"
        if ip_address:
            log_entry += f" (IP: {ip_address})"
        print(log_entry)
        
        # TODO: Add proper logging to file/database
        # with open('security.log', 'a') as f:
        #     f.write(log_entry + '\n')

# Convenience functions
def validate_user_input(input_data: Any, max_length: Optional[int] = None) -> bool:
    """Validate user input for security threats"""
    return DatabaseSecurity.validate_input(input_data, max_length)

def sanitize_user_input(input_data: Any, max_length: Optional[int] = None) -> Any:
    """Sanitize user input by removing dangerous characters"""
    return DatabaseSecurity.sanitize_input(input_data, max_length)

def create_safe_query(query_string: str, params: Optional[Dict] = None) -> str:
    """Create a safe SQL query using parameterized queries"""
    return DatabaseSecurity.safe_query(query_string, params)
