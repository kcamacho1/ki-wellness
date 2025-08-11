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
    
    // Store token in a more reliable way
    let currentToken = null;
    let widgetId = null;
    
    // Initialize Turnstile
    function initTurnstile(siteKey, theme = 'light', size = 'normal') {
        if (!siteKey) {
            console.error('Turnstile: Site key is required');
            return false;
        }
        
        TURNSTILE_CONFIG.siteKey = siteKey;
        TURNSTILE_CONFIG.theme = theme;
        TURNSTILE_CONFIG.size = size;
        
        console.log('Turnstile: Initializing with site key:', siteKey);
        
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
            console.log('Turnstile: Rendering widget...');
            widgetId = turnstile.render('.cf-turnstile', {
                sitekey: TURNSTILE_CONFIG.siteKey,
                theme: TURNSTILE_CONFIG.theme,
                size: TURNSTILE_CONFIG.size,
                callback: function(token) {
                    console.log('Turnstile: Challenge completed, token received');
                    currentToken = token;
                    // Also store in window for backward compatibility
                    window.turnstileToken = token;
                    
                    // Update the container to show completion status
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        container.setAttribute('data-completed', 'true');
                        container.setAttribute('data-token', token);
                    }
                },
                'expired-callback': function() {
                    console.log('Turnstile: Challenge expired');
                    currentToken = null;
                    window.turnstileToken = null;
                    
                    // Update the container to show expired status
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        container.setAttribute('data-completed', 'false');
                        container.removeAttribute('data-token');
                    }
                },
                'error-callback': function() {
                    console.error('Turnstile: Challenge error');
                    currentToken = null;
                    window.turnstileToken = null;
                    
                    // Update the container to show error status
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        container.setAttribute('data-completed', 'false');
                        container.removeAttribute('data-token');
                    }
                }
            });
            console.log('Turnstile: Widget rendered with ID:', widgetId);
        } catch (error) {
            console.error('Error rendering Turnstile:', error);
        }
    }
    
    // Get current Turnstile token
    function getToken() {
        // Try multiple sources for the token
        let token = currentToken || window.turnstileToken;
        
        // If still no token, try to get it from the widget directly
        if (!token && typeof turnstile !== 'undefined' && widgetId) {
            try {
                token = turnstile.getResponse(widgetId);
                if (token) {
                    currentToken = token;
                    window.turnstileToken = token;
                }
            } catch (error) {
                console.log('Turnstile: Could not get response from widget:', error);
            }
        }
        
        // Check if the container shows completion
        const container = document.querySelector('.cf-turnstile');
        if (container && container.getAttribute('data-completed') === 'true') {
            const containerToken = container.getAttribute('data-token');
            if (containerToken && !token) {
                token = containerToken;
                currentToken = token;
                window.turnstileToken = token;
            }
        }
        
        console.log('Turnstile: getToken() called, returning:', token ? 'TOKEN_PRESENT' : 'NO_TOKEN');
        return token;
    }
    
    // Reset Turnstile challenge
    function reset() {
        if (typeof turnstile !== 'undefined' && widgetId) {
            try {
                turnstile.reset(widgetId);
                currentToken = null;
                window.turnstileToken = null;
                
                // Update the container
                const container = document.querySelector('.cf-turnstile');
                if (container) {
                    container.setAttribute('data-completed', 'false');
                    container.removeAttribute('data-token');
                }
                
                console.log('Turnstile: Widget reset');
            } catch (error) {
                console.error('Error resetting Turnstile:', error);
            }
        }
    }
    
    // Validate form with Turnstile
    function validateForm(formElement) {
        const token = getToken();
        console.log('Turnstile: validateForm() called, token present:', !!token);
        
        if (!token) {
            // Check if Turnstile is actually required
            const container = document.querySelector('.cf-turnstile');
            if (container && container.getAttribute('data-completed') === 'true') {
                // Widget shows completed but no token - this is the bug we're fixing
                console.warn('Turnstile: Widget shows completed but no token found');
                return false;
            }
            
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
                console.log('Turnstile: Auto-initializing with site key:', siteKey);
                initTurnstile(siteKey);
            }
        }
    });
    
})();
