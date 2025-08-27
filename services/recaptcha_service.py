import os
import requests
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app

class ReCaptchaService:
    """Google reCAPTCHA v2 verification service"""
    
    def __init__(self):
        self.site_key = os.getenv('RECAPTCHA_SITE_KEY')
        self.secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        self.verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        
        if not self.site_key or not self.secret_key:
            print("⚠️ Warning: reCAPTCHA keys not found in environment variables")
            print("Please set RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY in your .env file")
    
    def verify_recaptcha(self, recaptcha_response: str, remote_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify reCAPTCHA response with Google
        
        Args:
            recaptcha_response: The response token from reCAPTCHA
            remote_ip: Optional IP address of the user
            
        Returns:
            Dictionary with verification results
        """
        if not self.secret_key:
            return {
                'success': False,
                'error': 'reCAPTCHA not configured',
                'error_codes': ['missing-secret-key']
            }
        
        if not recaptcha_response:
            return {
                'success': False,
                'error': 'No reCAPTCHA response provided',
                'error_codes': ['missing-input-response']
            }
        
        # Prepare verification request
        data = {
            'secret': self.secret_key,
            'response': recaptcha_response
        }
        
        if remote_ip:
            data['remoteip'] = remote_ip
        
        try:
            # Send verification request to Google
            response = requests.post(
                self.verify_url,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add human-readable error messages
                if not result.get('success', False):
                    error_codes = result.get('error-codes', [])
                    error_messages = {
                        'missing-input-secret': 'The secret parameter is missing',
                        'invalid-input-secret': 'The secret parameter is invalid or malformed',
                        'missing-input-response': 'The response parameter is missing',
                        'invalid-input-response': 'The response parameter is invalid or malformed',
                        'bad-request': 'The request is invalid or malformed',
                        'timeout-or-duplicate': 'The response is no longer valid: either is too old or has been used previously'
                    }
                    
                    error_message = 'reCAPTCHA verification failed'
                    if error_codes:
                        detailed_errors = [error_messages.get(code, code) for code in error_codes]
                        error_message = '; '.join(detailed_errors)
                    
                    result['error'] = error_message
                
                return result
            else:
                return {
                    'success': False,
                    'error': f'reCAPTCHA verification service error: {response.status_code}',
                    'error_codes': ['service-error']
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'reCAPTCHA verification timeout',
                'error_codes': ['timeout']
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'reCAPTCHA verification network error: {str(e)}',
                'error_codes': ['network-error']
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'reCAPTCHA verification error: {str(e)}',
                'error_codes': ['unknown-error']
            }
    
    def get_site_key(self) -> Optional[str]:
        """Get the reCAPTCHA site key for frontend use"""
        return self.site_key
    
    def is_configured(self) -> bool:
        """Check if reCAPTCHA is properly configured"""
        return bool(self.site_key and self.secret_key)

# Global reCAPTCHA service instance
recaptcha_service = ReCaptchaService()

def require_recaptcha(f):
    """Decorator to require reCAPTCHA verification for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not recaptcha_service.is_configured():
            # If reCAPTCHA is not configured, allow the request to proceed
            print("⚠️ Warning: reCAPTCHA not configured, skipping verification")
            return f(*args, **kwargs)
        
        if request.method == 'POST':
            # Get reCAPTCHA response from form data or JSON
            recaptcha_response = None
            
            if request.is_json:
                data = request.get_json() or {}
                recaptcha_response = data.get('g-recaptcha-response')
            else:
                recaptcha_response = request.form.get('g-recaptcha-response')
            
            if not recaptcha_response:
                return jsonify({
                    'success': False,
                    'error': 'reCAPTCHA verification required',
                    'error_code': 'missing-recaptcha'
                }), 400
            
            # Verify reCAPTCHA
            verification_result = recaptcha_service.verify_recaptcha(
                recaptcha_response, 
                request.remote_addr
            )
            
            if not verification_result.get('success', False):
                return jsonify({
                    'success': False,
                    'error': verification_result.get('error', 'reCAPTCHA verification failed'),
                    'error_code': 'recaptcha-failed'
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def verify_recaptcha_response(recaptcha_response: str, remote_ip: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to verify reCAPTCHA response"""
    return recaptcha_service.verify_recaptcha(recaptcha_response, remote_ip)

def get_recaptcha_site_key() -> Optional[str]:
    """Convenience function to get reCAPTCHA site key"""
    return recaptcha_service.get_site_key()
