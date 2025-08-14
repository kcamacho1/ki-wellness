/**
 * Toast Notification System
 * ========================
 * 
 * A modern, accessible toast notification system to replace JavaScript alerts.
 * Provides different types of notifications: success, error, warning, and info.
 * 
 * Features:
 * - Auto-dismiss after 5 seconds
 * - Manual dismiss with close button
 * - Keyboard accessible (ESC to close)
 * - Stacked notifications
 * - Smooth animations
 * - Mobile responsive
 */

class ToastNotifications {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.maxNotifications = 5;
        this.init();
    }

    /**
     * Initialize the toast container
     */
    init() {
        // Create container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }

        // Add keyboard listener for ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.dismissAll();
            }
        });
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type of notification (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds (default: 5000)
     */
    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        
        // Add to container
        this.container.appendChild(notification);
        this.notifications.push(notification);

        // Limit number of notifications
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.dismiss(oldest);
        }

        // Trigger entrance animation
        setTimeout(() => {
            notification.classList.add('translate-x-0', 'opacity-100');
        }, 10);

        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(notification);
            }, duration);
        }

        return notification;
    }

    /**
     * Create a notification element
     * @param {string} message - The message to display
     * @param {string} type - The type of notification
     * @returns {HTMLElement} The notification element
     */
    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `transform translate-x-full opacity-0 transition-all duration-300 ease-out bg-white border rounded-lg shadow-lg p-4 max-w-sm w-full`;
        
        // Add type-specific styling
        const typeStyles = {
            success: 'border-green-300 bg-green-50 text-green-800',
            error: 'border-red-300 bg-red-50 text-red-800',
            warning: 'border-yellow-300 bg-yellow-50 text-yellow-800',
            info: 'border-blue-300 bg-blue-50 text-blue-800'
        };
        
        notification.classList.add(...typeStyles[type].split(' '));

        // Get icon for type
        const icon = this.getIcon(type);
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    ${icon}
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium">${this.escapeHtml(message)}</p>
                </div>
                <div class="ml-4 flex-shrink-0">
                    <button type="button" class="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition-colors duration-200" aria-label="Close notification">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        // Add click handler for close button
        const closeBtn = notification.querySelector('button');
        closeBtn.addEventListener('click', () => {
            this.dismiss(notification);
        });

        return notification;
    }

    /**
     * Get icon for notification type
     * @param {string} type - The notification type
     * @returns {string} The SVG icon HTML
     */
    getIcon(type) {
        const icons = {
            success: `<svg class="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
            error: `<svg class="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>`,
            warning: `<svg class="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>`,
            info: `<svg class="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`
        };
        
        return icons[type] || icons.info;
    }

    /**
     * Dismiss a specific notification
     * @param {HTMLElement} notification - The notification element to dismiss
     */
    dismiss(notification) {
        if (!notification || !notification.parentNode) return;
        
        // Add exit animation
        notification.classList.remove('translate-x-0', 'opacity-100');
        notification.classList.add('translate-x-full', 'opacity-0');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            // Remove from notifications array
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Dismiss all notifications
     */
    dismissAll() {
        this.notifications.forEach(notification => {
            this.dismiss(notification);
        });
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - The text to escape
     * @returns {string} The escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Convenience methods for different notification types
     */
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// Create global instance
const Toast = new ToastNotifications();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastNotifications;
}
