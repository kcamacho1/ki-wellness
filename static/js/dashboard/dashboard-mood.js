// Dashboard Mood Management
// Handles mood tracking and display
class DashboardMood {
    constructor(core) {
        this.core = core;
    }

    updateDisplay(moodLogs) {
        if (moodLogs.length === 0) {
            // Show default state if no mood logged
            this.resetMoodDisplay();
            this.displayMoodHistory([]);
            return;
        }

        // Get the most recent mood for today
        const latestMood = moodLogs[moodLogs.length - 1];
        this.displayMood(latestMood.mood);
        this.highlightMoodButton(latestMood.mood);
        
        // Update mood history
        this.displayMoodHistory(moodLogs);
    }

    displayMood(moodValue) {
        const moodEmojis = {
            1: '😢',
            2: '😐', 
            3: '😊',
            4: '😃',
            5: '🤩'
        };
        
        const moodTexts = {
            1: 'Terrible',
            2: 'Okay',
            3: 'Good', 
            4: 'Great',
            5: 'Excellent'
        };

        const currentMoodEl = document.getElementById('current-mood');
        const moodTextEl = document.getElementById('mood-text');
        
        if (currentMoodEl) currentMoodEl.textContent = moodEmojis[moodValue] || '😊';
        if (moodTextEl) moodTextEl.textContent = moodTexts[moodValue] || 'Good';
    }

    resetMoodDisplay() {
        const currentMoodEl = document.getElementById('current-mood');
        const moodTextEl = document.getElementById('mood-text');
        
        if (currentMoodEl) currentMoodEl.textContent = '😊';
        if (moodTextEl) moodTextEl.textContent = 'Good';
    }

    displayMoodHistory(moodLogs) {
        const historyContainer = document.getElementById('mood-history');
        if (!historyContainer) {
            console.error('Mood history container not found');
            return;
        }

        if (!moodLogs || moodLogs.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center py-6 text-gray-500">
                    <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293L12 11l.707-.707A1 1 0 0113.414 10H15M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-900 mb-1">No mood entries for this date</p>
                    <p class="text-xs text-gray-500">Add your first mood entry above</p>
                </div>
            `;
            return;
        }

        const moodEmojis = {
            1: '😢',
            2: '😐', 
            3: '😊',
            4: '😃',
            5: '🤩'
        };
        
        const moodTexts = {
            1: 'Terrible',
            2: 'Okay',
            3: 'Good', 
            4: 'Great',
            5: 'Excellent'
        };

        const historyHTML = moodLogs.map(mood => {
            const time = new Date(mood.timestamp).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
            
            const emoji = moodEmojis[mood.mood] || '😊';
            const text = moodTexts[mood.mood] || 'Good';
            
            return `
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
                    <div class="flex items-center space-x-3">
                        <span class="text-2xl">${emoji}</span>
                        <div>
                            <p class="text-sm font-medium text-gray-900">${text}</p>
                            <p class="text-xs text-gray-500">${time}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Clear existing content and add new content
        historyContainer.innerHTML = historyHTML;
    }

    setMood(emoji, moodText, buttonElement) {
        const moodMap = {
            'Terrible': 1,
            'Okay': 2,
            'Good': 3,
            'Great': 4,
            'Excellent': 5
        };
        
        const moodValue = moodMap[moodText];
        if (moodValue) {
            // Log the mood to the server
            this.logMood(moodValue);
            
            // Add visual feedback to the selected button
            this.highlightSelectedButton(buttonElement);
        }
    }

    async logMood(mood) {
        const date = this.core.currentDate.toISOString().split('T')[0];
        
        try {
            const response = await fetch('/api/mood-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mood, date })
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast('Mood logged!', 'success');
                this.core.debouncedReload();
            } else {
                this.core.ui.showToast('Failed to log mood', 'error');
            }
        } catch (error) {
            console.error('Error logging mood:', error);
            this.core.ui.showToast('Failed to log mood', 'error');
        }
    }

    highlightSelectedButton(buttonElement) {
        // Reset all buttons first
        this.resetMoodButtons();
        
        // Highlight the selected button
        if (buttonElement) {
            const moodBtn = buttonElement.closest('.mood-btn');
            if (moodBtn) {
                moodBtn.classList.add('bg-ki-green-100', 'border-ki-green-300');
                moodBtn.classList.remove('hover:bg-gray-100');
            }
        }
    }

    highlightMoodButton(moodValue) {
        // Reset all buttons first
        this.resetMoodButtons();
        
        // Find and highlight the button for this mood value
        const moodButtons = document.querySelectorAll('.mood-btn');
        moodButtons.forEach(btn => {
            const buttonMoodText = btn.querySelector('[data-mood]')?.getAttribute('data-mood');
            const moodMap = {
                'Terrible': 1,
                'Okay': 2,
                'Good': 3,
                'Great': 4,
                'Excellent': 5
            };
            
            if (moodMap[buttonMoodText] === moodValue) {
                btn.classList.add('bg-ki-green-100', 'border-ki-green-300');
                btn.classList.remove('hover:bg-gray-100');
            }
        });
    }

    resetMoodButtons() {
        const moodButtons = document.querySelectorAll('.mood-btn');
        moodButtons.forEach(btn => {
            btn.classList.remove('bg-ki-green-100', 'border-ki-green-300');
            btn.classList.add('hover:bg-gray-100');
        });
    }
}

// Global function for mood logging (for backward compatibility)
function setMood(emoji, moodText) {
    if (window.dashboardManager) {
        window.dashboardManager.mood.setMood(emoji, moodText, event.target);
    }
}

function logMood(mood) {
    if (window.dashboardManager) {
        window.dashboardManager.mood.logMood(mood);
    }
}

// Make available globally
window.DashboardMood = DashboardMood;
