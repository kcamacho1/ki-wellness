/**
 * Turnstile Module for Cloudflare Turnstile Integration
 * This module is only loaded when Turnstile is enabled (not on localhost/dev)
 */

(function() {
    'use strict';
    
    // Turnstile configuration
    const TURNSTILE_CONFIG = {
        siteKey: null,
        theme: 'light',
        size: 'normal'
    };
    
    // Initialize Turnstile
    function initTurnstile(siteKey, theme = 'light', size = 'normal') {
        if (!siteKey) {
            console.error('Turnstile: Site key is required');
            return false;
        }
        
        TURNSTILE_CONFIG.siteKey = siteKey;
        TURNSTILE_CONFIG.theme = theme;
        TURNSTILE_CONFIG.size = size;
        
        // Wait for Turnstile to be ready
        if (typeof turnstile !== 'undefined') {
            renderTurnstile();
        } else {
            // Poll for Turnstile to be available
            const checkTurnstile = setInterval(() => {
                if (typeof turnstile !== 'undefined') {
                    clearInterval(checkTurnstile);
                    renderTurnstile();
                }
            }, 100);
        }
        
        return true;
    }
    
    // Render Turnstile widget
    function renderTurnstile() {
        try {
            turnstile.render('.cf-turnstile', {
                sitekey: TURNSTILE_CONFIG.siteKey,
                theme: TURNSTILE_CONFIG.theme,
                size: TURNSTILE_CONFIG.size,
                callback: function(token) {
                    console.log('Turnstile challenge completed');
                    // Store the token for form submission
                    window.turnstileToken = token;
                },
                'expired-callback': function() {
                    console.log('Turnstile challenge expired');
                    window.turnstileToken = null;
                },
                'error-callback': function() {
                    console.error('Turnstile challenge error');
                    window.turnstileToken = null;
                }
            });
        } catch (error) {
            console.error('Error rendering Turnstile:', error);
        }
    }
    
    // Get current Turnstile token
    function getToken() {
        return window.turnstileToken || null;
    }
    
    // Reset Turnstile challenge
    function reset() {
        if (typeof turnstile !== 'undefined') {
            try {
                turnstile.reset();
                window.turnstileToken = null;
            } catch (error) {
                console.error('Error resetting Turnstile:', error);
            }
        }
    }
    
    // Validate form with Turnstile
    function validateForm(formElement) {
        const token = getToken();
        if (!token) {
            alert('Please complete the security verification.');
            return false;
        }
        return true;
    }
    
    // Add Turnstile validation to forms
    function addFormValidation(formSelector = 'form') {
        const forms = document.querySelectorAll(formSelector);
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }
    
    // Public API
    window.TurnstileModule = {
        init: initTurnstile,
        getToken: getToken,
        reset: reset,
        validateForm: validateForm,
        addFormValidation: addFormValidation
    };
    
    // Auto-initialize if data attributes are present
    document.addEventListener('DOMContentLoaded', function() {
        const turnstileContainer = document.querySelector('.cf-turnstile');
        if (turnstileContainer) {
            const siteKey = turnstileContainer.dataset.sitekey;
            if (siteKey) {
                initTurnstile(siteKey);
            }
        }
    });
    
})();
