class AdminDashboardManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateLastUpdatedTime();
    }

    setupEventListeners() {
        // Toggle switches
        document.getElementById('new-accounts-toggle').addEventListener('change', (e) => {
            this.updateSetting('new_accounts_enabled', e.target.checked);
        });

        document.getElementById('maintenance-toggle').addEventListener('change', (e) => {
            this.updateSetting('maintenance_mode', e.target.checked);
        });

        // Max users input
        document.getElementById('update-max-users').addEventListener('click', () => {
            const maxUsers = document.getElementById('max-users-input').value;
            this.updateSetting('max_users', maxUsers);
        });

        // Allowed emails
        document.getElementById('update-allowed-emails').addEventListener('click', () => {
            const allowedEmails = document.getElementById('allowed-emails-input').value;
            this.updateSetting('allowed_emails', allowedEmails);
        });

        document.getElementById('clear-allowed-emails').addEventListener('click', () => {
            document.getElementById('allowed-emails-input').value = '';
            this.updateSetting('allowed_emails', '');
        });

        // Payment type settings
        document.getElementById('update-payment-type').addEventListener('click', () => {
            const selectedPaymentType = document.querySelector('input[name="payment-type"]:checked').value;
            this.updateSetting('human_help_payment_type', selectedPaymentType);
        });

        // Calendly link
        document.getElementById('update-calendly-link').addEventListener('click', () => {
            const calendlyLink = document.getElementById('calendly-link-input').value;
            this.updateSetting('calendly_link', calendlyLink);
        });

        // Quick actions
        document.getElementById('refresh-stats').addEventListener('click', () => {
            this.refreshStatistics();
        });

        document.getElementById('export-data').addEventListener('click', () => {
            this.exportData();
        });
    }

    async updateSetting(key, value) {
        try {
            const response = await fetch('/api/admin/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    key: key,
                    value: value
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Setting updated successfully!', 'success');
                this.updateLastUpdatedTime();
                
                // Show visual feedback for specific settings
                if (key === 'new_accounts_enabled') {
                    const status = value ? 'enabled' : 'disabled';
                    this.showNotification(`New account registration ${status}`, 'info');
                } else if (key === 'maintenance_mode') {
                    const status = value ? 'enabled' : 'disabled';
                    this.showNotification(`Maintenance mode ${status}`, 'warning');
                }
            } else {
                this.showNotification('Failed to update setting: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error updating setting:', error);
            this.showNotification('Error updating setting. Please try again.', 'error');
        }
    }

    async refreshStatistics() {
        try {
            // Show loading state
            const button = document.getElementById('refresh-stats');
            const originalText = button.textContent;
            button.textContent = '🔄 Refreshing...';
            button.disabled = true;

            // Reload the page to get fresh statistics
            setTimeout(() => {
                window.location.reload();
            }, 1000);

        } catch (error) {
            console.error('Error refreshing statistics:', error);
            this.showNotification('Error refreshing statistics. Please try again.', 'error');
            
            // Reset button
            const button = document.getElementById('refresh-stats');
            button.textContent = '🔄 Refresh Statistics';
            button.disabled = false;
        }
    }

    async exportData() {
        try {
            this.showNotification('Export functionality coming soon!', 'info');
            // TODO: Implement data export functionality
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showNotification('Error exporting data. Please try again.', 'error');
        }
    }

    updateLastUpdatedTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const dateString = now.toLocaleDateString();
        document.getElementById('last-updated-time').textContent = `${dateString} at ${timeString}`;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-xl shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
        
        // Set background color based on type
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        notification.className += ` ${colors[type] || colors.info}`;
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    ${this.getNotificationIcon(type)}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button class="flex-shrink-0 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>',
            info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        
        return icons[type] || icons.info;
    }
}

// Initialize admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminDashboardManager();
});
