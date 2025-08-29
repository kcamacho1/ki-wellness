// Dashboard Water Management
// Handles water intake tracking and display
class DashboardWater {
    constructor(core) {
        this.core = core;
        this.quickWaterAmount = 8; // Default to 8 oz
    }

    updateDisplay(waterLogs) {
        const totalWater = waterLogs.reduce((sum, log) => sum + log.amount, 0);
        const goal = 64; // 64 oz daily goal
        const percentage = Math.min((totalWater / goal) * 100, 100);

        const display = document.getElementById('water-display');
        const progress = document.getElementById('water-progress');
        
        if (display) display.textContent = `${Math.round(totalWater)} oz`;
        if (progress) progress.style.width = `${percentage}%`;
    }

    async logWater() {
        const amountInput = document.getElementById('water-amount');
        const amount = parseFloat(amountInput?.value) || 0;
        
        if (amount <= 0) {
            this.core.ui.showToast('Please enter a valid water amount', 'warning');
            return;
        }

        try {
            const date = this.core.currentDate.toISOString().split('T')[0];
            const response = await fetch('/api/water-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount, date })
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast('Water intake logged!', 'success');
                this.core.debouncedReload();
                
                // Clear the input
                if (amountInput) amountInput.value = '';
            } else {
                this.core.ui.showToast('Failed to log water intake', 'error');
            }
        } catch (error) {
            console.error('Error logging water:', error);
            this.core.ui.showToast('Failed to log water intake', 'error');
        }
    }

    async addQuickWater(amount = null) {
        const waterAmount = amount || this.quickWaterAmount;
        const date = this.core.currentDate.toISOString().split('T')[0];

        try {
            const response = await fetch('/api/water-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: waterAmount, date: date })
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast(`Added ${waterAmount} oz of water!`, 'success');
                this.core.debouncedReload();
            } else {
                this.core.ui.showToast('Failed to log water intake', 'error');
            }
        } catch (error) {
            console.error('Error logging water:', error);
            this.core.ui.showToast('Failed to log water intake', 'error');
        }
    }

    loadWaterSettings() {
        try {
            const saved = localStorage.getItem('quickWaterAmount');
            if (saved) {
                this.quickWaterAmount = parseInt(saved);
            }
        } catch (error) {
            console.error('Error loading water settings:', error);
        }
    }

    saveWaterSettings() {
        const amountInput = document.getElementById('water-quick-amount');
        const amount = parseInt(amountInput?.value) || 8;
        
        this.quickWaterAmount = amount;
        
        try {
            localStorage.setItem('quickWaterAmount', amount.toString());
            this.core.ui.showToast('Water settings saved!', 'success');
            this.closeWaterSettingsModal();
        } catch (error) {
            console.error('Error saving water settings:', error);
            this.core.ui.showToast('Failed to save water settings', 'error');
        }
    }

    getQuickWaterAmount() {
        return this.quickWaterAmount;
    }

    openWaterSettingsModal() {
        const modal = document.getElementById('water-settings-modal');
        const amountInput = document.getElementById('water-quick-amount');
        
        // Load current amount
        if (amountInput) amountInput.value = this.quickWaterAmount;
        
        if (modal) modal.classList.remove('hidden');
    }

    closeWaterSettingsModal() {
        const modal = document.getElementById('water-settings-modal');
        if (modal) modal.classList.add('hidden');
    }
}

// Global functions for water management (for backward compatibility)
function logWater() {
    if (window.dashboardManager) {
        window.dashboardManager.water.logWater();
    }
}

function addQuickWater(amount = null) {
    if (window.dashboardManager) {
        window.dashboardManager.water.addQuickWater(amount);
    }
}

function openWaterSettingsModal() {
    if (window.dashboardManager) {
        window.dashboardManager.water.openWaterSettingsModal();
    }
}

function closeWaterSettingsModal() {
    if (window.dashboardManager) {
        window.dashboardManager.water.closeWaterSettingsModal();
    }
}

function saveWaterSettings() {
    if (window.dashboardManager) {
        window.dashboardManager.water.saveWaterSettings();
    }
}

// Make available globally
window.DashboardWater = DashboardWater;
