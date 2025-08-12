/**
 * Development Bypass Module
 * Provides a mock reCAPTCHA interface when running on localhost/development
 */

(function() {
    'use strict';
    
    console.log('🔧 Development mode: reCAPTCHA bypass module loaded');
    
    // Mock reCAPTCHA interface for development
    window.grecaptcha = {
        ready: function(callback) {
            console.log('🔧 Development mode: Mock reCAPTCHA ready');
            // Execute callback immediately in development
            if (typeof callback === 'function') {
                callback();
            }
        },
        execute: function(siteKey, options) {
            console.log('🔧 Development mode: Mock reCAPTCHA execute called');
            console.log('🔧 Site key:', siteKey);
            console.log('🔧 Options:', options);
            
            // Return a promise that resolves with a mock token
            return Promise.resolve('dev-bypass-token-' + Date.now());
        },
        render: function(element, options) {
            console.log('🔧 Development mode: Mock reCAPTCHA render called');
            return 'dev-widget-id';
        }
    };
    
    // Add development indicator to the page
    document.addEventListener('DOMContentLoaded', function() {
        const recaptchaContainer = document.querySelector('.g-recaptcha');
        if (recaptchaContainer) {
            recaptchaContainer.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center mb-2">
                        <svg class="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span class="text-green-800 font-medium">Development Mode</span>
                    </div>
                    <p class="text-sm text-green-700">Security verification bypassed for local development</p>
                    <p class="text-xs text-green-600 mt-1">reCAPTCHA v3 will be enabled in production</p>
                </div>
            `;
        }
        
        // Also check for any forms that might need the bypass
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (form.querySelector('.g-recaptcha')) {
                console.log('🔧 Development mode: Form with reCAPTCHA detected, bypass active');
            }
        });
    });
    
})();
