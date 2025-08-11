/**
 * Development Bypass Module
 * Provides a mock Turnstile interface when running on localhost/development
 */

(function() {
    'use strict';
    
    console.log('🔧 Development mode: Turnstile bypass module loaded');
    
    // Mock Turnstile module for development
    window.TurnstileModule = {
        init: function(siteKey, theme, size) {
            console.log('🔧 Development mode: Mock Turnstile initialized');
            return true;
        },
        getToken: function() {
            // Always return a mock token in development
            return 'dev-bypass-token-' + Date.now();
        },
        reset: function() {
            console.log('🔧 Development mode: Mock Turnstile reset');
        },
        validateForm: function(formElement) {
            // Always return true in development
            return true;
        },
        addFormValidation: function(formSelector) {
            console.log('🔧 Development mode: Mock form validation added');
        }
    };
    
    // Add development indicator to the page
    document.addEventListener('DOMContentLoaded', function() {
        const turnstileContainer = document.querySelector('.cf-turnstile');
        if (turnstileContainer) {
            turnstileContainer.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center mb-2">
                        <svg class="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span class="text-green-800 font-medium">Development Mode</span>
                    </div>
                    <p class="text-sm text-green-700">Security verification bypassed for local development</p>
                </div>
            `;
        }
    });
    
})();
