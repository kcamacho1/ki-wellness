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
    
    // Store token in a more reliable way with multiple fallbacks
    let currentToken = null;
    let widgetId = null;
    let isInitialized = false;
    let initializationPromise = null;
    
    // Initialize Turnstile with proper error handling
    function initTurnstile(siteKey, theme = 'light', size = 'normal') {
        if (!siteKey) {
            console.error('Turnstile: Site key is required');
            return Promise.reject(new Error('Site key is required'));
        }
        
        // If already initializing, return the existing promise
        if (initializationPromise) {
            return initializationPromise;
        }
        
        // If already initialized, return resolved promise
        if (isInitialized) {
            return Promise.resolve();
        }
        
        TURNSTILE_CONFIG.siteKey = siteKey;
        TURNSTILE_CONFIG.theme = theme;
        TURNSTILE_CONFIG.size = size;
        
        console.log('Turnstile: Initializing with site key:', siteKey);
        
        initializationPromise = new Promise((resolve, reject) => {
            // Wait for Turnstile to be ready
            if (typeof turnstile !== 'undefined') {
                try {
                    renderTurnstile();
                    resolve();
                } catch (error) {
                    reject(error);
                }
            } else {
                // Poll for Turnstile to be available with timeout
                let attempts = 0;
                const maxAttempts = 50; // 5 seconds max wait
                
                const checkTurnstile = setInterval(() => {
                    attempts++;
                    if (typeof turnstile !== 'undefined') {
                        clearInterval(checkTurnstile);
                        try {
                            renderTurnstile();
                            resolve();
                        } catch (error) {
                            reject(error);
                        }
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkTurnstile);
                        reject(new Error('Turnstile failed to load within timeout'));
                    }
                }, 100);
            }
        });
        
        return initializationPromise;
    }
    
    // Render Turnstile widget with comprehensive error handling
    function renderTurnstile() {
        try {
            console.log('Turnstile: Rendering widget...');
            
            // Clear any existing widget
            const container = document.querySelector('.cf-turnstile');
            if (container) {
                container.innerHTML = '';
            }
            
            widgetId = turnstile.render('.cf-turnstile', {
                sitekey: TURNSTILE_CONFIG.siteKey,
                theme: TURNSTILE_CONFIG.theme,
                size: TURNSTILE_CONFIG.size,
                callback: function(token) {
                    console.log('Turnstile: Challenge completed, token received:', token ? 'TOKEN_PRESENT' : 'NO_TOKEN');
                    
                    if (token) {
                        currentToken = token;
                        // Store in multiple locations for reliability
                        window.turnstileToken = token;
                        localStorage.setItem('turnstileToken', token);
                        
                        // Update the container to show completion status
                        if (container) {
                            container.setAttribute('data-completed', 'true');
                            container.setAttribute('data-token', token);
                            container.setAttribute('data-status', 'success');
                        }
                        
                        // Dispatch custom event for other components
                        window.dispatchEvent(new CustomEvent('turnstileCompleted', { 
                            detail: { token: token, widgetId: widgetId } 
                        }));
                    } else {
                        console.warn('Turnstile: Callback received but no token provided');
                        currentToken = null;
                        window.turnstileToken = null;
                        localStorage.removeItem('turnstileToken');
                    }
                },
                'expired-callback': function() {
                    console.log('Turnstile: Challenge expired');
                    currentToken = null;
                    window.turnstileToken = null;
                    localStorage.removeItem('turnstileToken');
                    
                    // Update the container to show expired status
                    if (container) {
                        container.setAttribute('data-completed', 'false');
                        container.removeAttribute('data-token');
                        container.setAttribute('data-status', 'expired');
                    }
                    
                    // Dispatch custom event
                    window.dispatchEvent(new CustomEvent('turnstileExpired', { 
                        detail: { widgetId: widgetId } 
                    }));
                },
                'error-callback': function() {
                    console.error('Turnstile: Challenge error');
                    currentToken = null;
                    window.turnstileToken = null;
                    localStorage.removeItem('turnstileToken');
                    
                    // Update the container to show error status
                    if (container) {
                        container.setAttribute('data-completed', 'false');
                        container.removeAttribute('data-token');
                        container.setAttribute('data-status', 'error');
                    }
                    
                    // Dispatch custom event
                    window.dispatchEvent(new CustomEvent('turnstileError', { 
                        detail: { widgetId: widgetId } 
                    }));
                }
            });
            
            console.log('Turnstile: Widget rendered with ID:', widgetId);
            isInitialized = true;
            
        } catch (error) {
            console.error('Error rendering Turnstile:', error);
            isInitialized = false;
            throw error;
        }
    }
    
    // Get current Turnstile token with comprehensive fallback strategy
    function getToken() {
        // Priority 1: Current token in memory
        let token = currentToken;
        
        // Priority 2: Window object token
        if (!token && window.turnstileToken) {
            token = window.turnstileToken;
            currentToken = token; // Cache it
        }
        
        // Priority 3: Local storage token
        if (!token) {
            const storedToken = localStorage.getItem('turnstileToken');
            if (storedToken) {
                token = storedToken;
                currentToken = token; // Cache it
                window.turnstileToken = token; // Update window object
            }
        }
        
        // Priority 4: Widget response (most reliable)
        if (!token && typeof turnstile !== 'undefined' && widgetId) {
            try {
                const widgetToken = turnstile.getResponse(widgetId);
                if (widgetToken) {
                    token = widgetToken;
                    currentToken = token;
                    window.turnstileToken = token;
                    localStorage.setItem('turnstileToken', token);
                }
            } catch (error) {
                console.log('Turnstile: Could not get response from widget:', error);
            }
        }
        
        // Priority 5: Container attributes
        if (!token) {
            const container = document.querySelector('.cf-turnstile');
            if (container && container.getAttribute('data-completed') === 'true') {
                const containerToken = container.getAttribute('data-token');
                if (containerToken) {
                    token = containerToken;
                    currentToken = token;
                    window.turnstileToken = token;
                    localStorage.setItem('turnstileToken', token);
                }
            }
        }
        
        // Log the result for debugging
        if (token) {
            console.log('Turnstile: getToken() successful, token length:', token.length);
        } else {
            console.warn('Turnstile: getToken() failed - no token found from any source');
        }
        
        return token;
    }
    
    // Reset Turnstile challenge
    function reset() {
        if (typeof turnstile !== 'undefined' && widgetId) {
            try {
                turnstile.reset(widgetId);
                currentToken = null;
                window.turnstileToken = null;
                localStorage.removeItem('turnstileToken');
                
                // Update the container
                const container = document.querySelector('.cf-turnstile');
                if (container) {
                    container.setAttribute('data-completed', 'false');
                    container.removeAttribute('data-token');
                    container.setAttribute('data-status', 'reset');
                }
                
                console.log('Turnstile: Widget reset');
            } catch (error) {
                console.error('Error resetting Turnstile:', error);
            }
        }
    }
    
    // Validate form with Turnstile - enhanced version
    function validateForm(formElement) {
        const token = getToken();
        console.log('Turnstile: validateForm() called, token present:', !!token);
        
        if (!token) {
            // Check if Turnstile is actually required
            const container = document.querySelector('.cf-turnstile');
            if (container) {
                const status = container.getAttribute('data-status');
                const completed = container.getAttribute('data-completed');
                
                console.warn('Turnstile: Validation failed. Status:', status, 'Completed:', completed);
                
                if (completed === 'true' && !token) {
                    console.error('Turnstile: CRITICAL BUG - Widget shows completed but no token found');
                    // Try to recover by forcing a reset
                    reset();
                }
            }
            
            return false;
        }
        return true;
    }
    
    // Add Turnstile validation to forms with enhanced error handling
    function addFormValidation(formSelector = 'form') {
        const forms = document.querySelectorAll(formSelector);
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                    
                    // Show user-friendly error message
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        container.style.border = '2px solid #ef4444';
                        container.style.backgroundColor = '#fef2f2';
                        
                        // Add error message below the widget
                        let errorMsg = container.nextElementSibling;
                        if (!errorMsg || !errorMsg.classList.contains('turnstile-error')) {
                            errorMsg = document.createElement('div');
                            errorMsg.className = 'turnstile-error text-red-600 text-sm mt-2 text-center';
                            errorMsg.textContent = 'Please complete the security verification above';
                            container.parentNode.insertBefore(errorMsg, container.nextSibling);
                        }
                    }
                    
                    return false;
                }
            });
        });
    }
    
    // Check if Turnstile is ready and working
    function isReady() {
        return isInitialized && typeof turnstile !== 'undefined' && widgetId;
    }
    
    // Get detailed status for debugging
    function getStatus() {
        return {
            isInitialized: isInitialized,
            hasTurnstile: typeof turnstile !== 'undefined',
            hasWidget: !!widgetId,
            hasToken: !!getToken(),
            containerStatus: (() => {
                const container = document.querySelector('.cf-turnstile');
                if (container) {
                    return {
                        completed: container.getAttribute('data-completed'),
                        status: container.getAttribute('data-status'),
                        hasToken: container.getAttribute('data-token')
                    };
                }
                return null;
            })()
        };
    }
    
    // Public API
    window.TurnstileModule = {
        init: initTurnstile,
        getToken: getToken,
        reset: reset,
        validateForm: validateForm,
        addFormValidation: addFormValidation,
        isReady: isReady,
        getStatus: getStatus
    };
    
    // Auto-initialize if data attributes are present
    document.addEventListener('DOMContentLoaded', function() {
        const turnstileContainer = document.querySelector('.cf-turnstile');
        if (turnstileContainer) {
            const siteKey = turnstileContainer.dataset.sitekey;
            if (siteKey) {
                console.log('Turnstile: Auto-initializing with site key:', siteKey);
                initTurnstile(siteKey).catch(error => {
                    console.error('Turnstile: Auto-initialization failed:', error);
                });
            }
        }
    });
    
})();
