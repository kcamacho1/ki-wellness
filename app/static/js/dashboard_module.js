/**
 * Ki Wellness - Dashboard Module
 * =============================
 * 
 * Modular JavaScript functions for dashboard functionality
 * Reuses existing components and follows established patterns
 * 
 * Author: Ki Wellness Team
 * Version: 1.0
 */

// Session Management Class
class SessionManager {
    constructor() {
        this.SESSION_TIMEOUT = 3600000; // 1 hour in milliseconds
        this.WARNING_TIME = 300000; // 5 minutes before timeout
        this.sessionTimer = null;
        this.warningTimer = null;
    }

    /**
     * Initialize session management
     */
    init() {
        this.resetSessionTimer();
        this.setupActivityListeners();
    }

    /**
     * Reset session timers
     */
    resetSessionTimer() {
        // Clear existing timers
        if (this.sessionTimer) clearTimeout(this.sessionTimer);
        if (this.warningTimer) clearTimeout(this.warningTimer);
        
        // Set warning timer (5 minutes before timeout)
        this.warningTimer = setTimeout(() => {
            this.showSessionWarning();
        }, this.SESSION_TIMEOUT - this.WARNING_TIME);
        
        // Set session timeout timer
        this.sessionTimer = setTimeout(() => {
            this.logoutUser();
        }, this.SESSION_TIMEOUT);
    }

    /**
     * Show session warning modal
     */
    showSessionWarning() {
        // Create warning modal
        const warningModal = document.createElement('div');
        warningModal.id = 'session-warning-modal';
        warningModal.innerHTML = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 max-w-md mx-4">
                    <div class="flex items-center mb-4">
                        <div class="flex-shrink-0">
                            <svg class="h-6 w-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-medium text-gray-900">Session Expiring Soon</h3>
                        </div>
                    </div>
                    <div class="mb-4">
                        <p class="text-sm text-gray-600">
                            Your session will expire in 5 minutes for security reasons. 
                            Click "Stay Logged In" to extend your session.
                        </p>
                    </div>
                    <div class="flex justify-end space-x-3">
                        <button onclick="sessionManager.logoutUser()" class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                            Logout Now
                        </button>
                        <button onclick="sessionManager.extendSession()" class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700">
                            Stay Logged In
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(warningModal);
    }

    /**
     * Extend session
     */
    async extendSession() {
        // Remove warning modal
        const modal = document.getElementById('session-warning-modal');
        if (modal) modal.remove();
        
        try {
            const response = await fetch('/extend-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                // Reset timers
                this.resetSessionTimer();
                console.log('Session extended successfully');
            } else {
                this.logoutUser();
            }
        } catch (error) {
            console.error('Error extending session:', error);
            this.logoutUser();
        }
    }

    /**
     * Logout user
     */
    logoutUser() {
        window.location.href = '/logout';
    }

    /**
     * Setup activity listeners
     */
    setupActivityListeners() {
        ['click', 'keypress', 'scroll', 'mousemove'].forEach(event => {
            document.addEventListener(event, () => this.resetSessionTimer(), { passive: true });
        });
    }
}

// Chart Management Class
class ChartManager {
    constructor() {
        this.charts = new Map();
    }

    /**
     * Create or update a chart
     */
    createChart(canvasId, type, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas with id '${canvasId}' not found`);
            return null;
        }

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        // Create new chart
        const chart = new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                ...options
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Update chart data
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    /**
     * Destroy a chart
     */
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }

    /**
     * Create macronutrients pie chart
     */
    createMacrosChart(protein, carbs, fat) {
        const total = protein + carbs + fat;
        
        if (total === 0) {
            // Show empty chart
            const chart = this.createChart('macrosChart', 'doughnut', {
                datasets: [{
                    data: [1],
                    backgroundColor: ['#e5e7eb'],
                    borderWidth: 0
                }]
            }, {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%'
            });
            
            // Make chart globally accessible
            window.macrosChart = chart;
            return chart;
        }

        const chart = this.createChart('macrosChart', 'doughnut', {
            datasets: [{
                data: [protein, carbs, fat],
                backgroundColor: ['#ef4444', '#eab308', '#22c55e'],
                borderWidth: 0
            }]
        }, {
            plugins: {
                legend: {
                    display: false
                }
            },
            cutout: '70%'
        });
        
        // Make chart globally accessible
        window.macrosChart = chart;
        return chart;
    }
}

// Modal Management Class
class ModalManager {
    constructor() {
        this.activeModal = null;
    }

    /**
     * Show modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            this.activeModal = modalId;
        }
    }

    /**
     * Hide modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
            this.activeModal = null;
        }
    }

    /**
     * Hide active modal
     */
    hideActiveModal() {
        if (this.activeModal) {
            this.hideModal(this.activeModal);
        }
    }
}

// Loading State Management Class
class LoadingManager {
    constructor() {
        this.loadingStates = new Map();
    }

    /**
     * Show loading state
     */
    showLoading(elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (element) {
            const originalContent = element.innerHTML;
            this.loadingStates.set(elementId, originalContent);
            
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-mint-green mx-auto"></div>
                    <p class="text-sm text-gray-600 mt-2">${message}</p>
                </div>
            `;
        }
    }

    /**
     * Hide loading state
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element && this.loadingStates.has(elementId)) {
            element.innerHTML = this.loadingStates.get(elementId);
            this.loadingStates.delete(elementId);
        }
    }

    /**
     * Show error state
     */
    showError(elementId, message = 'An error occurred') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="text-red-500 mb-2">
                        <svg class="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                    </div>
                    <p class="text-sm text-gray-600">${message}</p>
                </div>
            `;
        }
    }
}

// API Service Class
class APIService {
    /**
     * Make API request with error handling
     */
    static async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed for ${url}:`, error);
            throw error;
        }
    }

    /**
     * Get user profile data
     */
    static async getProfileData() {
        return this.request('/profile/data');
    }

    /**
     * Get food journal entries
     */
    static async getFoodEntries(startDate, endDate) {
        return this.request(`/food-journal/entries?start_date=${startDate}&end_date=${endDate}`);
    }

    /**
     * Get mood entries
     */
    static async getMoodEntries(startDate, endDate) {
        return this.request(`/dashboard/mood/entries?start_date=${startDate}&end_date=${endDate}`);
    }

    /**
     * Get patterns analysis
     */
    static async getPatternsAnalysis() {
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        return this.request(`/dashboard/patterns?browser_timezone=${encodeURIComponent(browserTimezone)}`);
    }

    /**
     * Add water intake
     */
    static async addWaterIntake(targetDate = null) {
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const requestBody = { browser_timezone: browserTimezone };
        
        if (targetDate) {
            requestBody.target_date = targetDate.toISOString();
        }
        
        return this.request('/dashboard/water/add', {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
    }

    /**
     * Add mood entry
     */
    static async addMoodEntry(mood, notes, targetDate = null) {
        // Convert text mood to numeric score
        const moodScoreMap = {
            '😊 Great': 9,
            '😌 Good': 7,
            '😐 Neutral': 5,
            '😔 Down': 3,
            '😤 Stressed': 2,
            '😴 Tired': 4
        };
        
        const moodScore = moodScoreMap[mood] || 5; // Default to neutral if not found
        
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const requestBody = {
            mood_score: moodScore,
            notes: notes,
            browser_timezone: browserTimezone
        };
        
        if (targetDate) {
            requestBody.target_date = targetDate.toISOString();
        }
        
        return this.request('/dashboard/mood/add', {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
    }

    /**
     * Refresh patterns analysis
     */
    static async refreshPatterns() {
        return this.request('/dashboard/patterns/refresh', {
            method: 'POST'
        });
    }
}

// Utility Functions
class DashboardUtils {
    /**
     * Format date in user's timezone
     */
    static formatDateInUserTimezone(dateString) {
        try {
            const date = new Date(dateString);
            
            if (isNaN(date.getTime())) {
                return dateString;
            }
            
            return date.toLocaleDateString('en-US', { 
                weekday: 'short',
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } catch (error) {
            console.error('Error formatting date:', error);
            return dateString;
        }
    }

    /**
     * Get today's date string in YYYY-MM-DD format
     */
    static getTodayString() {
        return new Date().toLocaleDateString('en-CA');
    }

    /**
     * Calculate average mood from mood array
     */
    static calculateAverageMood(moods) {
        if (moods.length === 0) {
            return { emoji: '😐', text: 'No mood data' };
        }

        const moodScores = {
            'happy': 5, 'great': 5, 'excellent': 5, 'amazing': 5,
            'good': 4, 'fine': 4, 'okay': 4, 'alright': 4,
            'neutral': 3, 'meh': 3, 'average': 3,
            'sad': 2, 'bad': 2, 'terrible': 2, 'awful': 2,
            'angry': 1, 'frustrated': 1, 'stressed': 1
        };

        let totalScore = 0;
        let validMoods = 0;

        moods.forEach(mood => {
            const lowerMood = mood.toLowerCase();
            for (const [key, score] of Object.entries(moodScores)) {
                if (lowerMood.includes(key)) {
                    totalScore += score;
                    validMoods++;
                    break;
                }
            }
        });

        if (validMoods === 0) {
            return { emoji: '😐', text: 'Neutral' };
        }

        const averageScore = totalScore / validMoods;
        
        if (averageScore >= 4.5) {
            return { emoji: '😄', text: 'Excellent' };
        } else if (averageScore >= 3.5) {
            return { emoji: '🙂', text: 'Good' };
        } else if (averageScore >= 2.5) {
            return { emoji: '😐', text: 'Neutral' };
        } else if (averageScore >= 1.5) {
            return { emoji: '😔', text: 'Not Great' };
        } else {
            return { emoji: '😢', text: 'Poor' };
        }
    }

    /**
     * Show success feedback on element
     */
    static showSuccessFeedback(elementId, duration = 1000) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('text-green-600');
            setTimeout(() => {
                element.classList.remove('text-green-600');
            }, duration);
        }
    }

    /**
     * Show scale animation on element
     */
    static showScaleAnimation(elementId, duration = 200) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('scale-110');
            setTimeout(() => {
                element.classList.remove('scale-110');
            }, duration);
        }
    }
}

// Share functionality (reusing existing patterns)
class ShareManager {
    /**
     * Share tile functionality
     */
    static async shareTile(tileType) {
        try {
            const shareButton = document.querySelector(`[data-tile="${tileType}"]`);
            const originalContent = shareButton.innerHTML;
            
            // Show loading state
            shareButton.innerHTML = `
                <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
            `;
            shareButton.disabled = true;
            
            // Find the tile element
            let tileElement = null;
            let tileTitle = '';
            
            switch(tileType) {
                case 'water':
                    tileElement = document.querySelector('[data-tile="water"]').closest('.bg-white');
                    tileTitle = 'Water Intake';
                    break;
                case 'macros':
                    tileElement = document.querySelector('[data-tile="macros"]').closest('.bg-white');
                    tileTitle = 'Macronutrients';
                    break;
                case 'mood':
                    tileElement = document.querySelector('[data-tile="mood"]').closest('.bg-white');
                    tileTitle = 'Today\'s Mood';
                    break;
            }

            if (!tileElement) {
                throw new Error('Tile element not found');
            }

            // Hide share buttons before taking screenshot
            const shareButtons = tileElement.querySelectorAll('.share-btn');
            const originalDisplayStates = [];
            shareButtons.forEach(button => {
                originalDisplayStates.push(button.style.display);
                button.style.display = 'none';
            });

            // Create screenshot using html2canvas
            const html2canvas = window.html2canvas || await this.loadHtml2Canvas();
            
            const tileCanvas = await html2canvas(tileElement, {
                backgroundColor: '#ffffff',
                scale: 3,
                useCORS: true,
                allowTaint: true,
                logging: false,
                removeContainer: true
            });

            // Add logo watermark
            const finalCanvas = await this.addLogoWatermark(tileCanvas);

            // Convert to blob
            const blob = await new Promise(resolve => {
                finalCanvas.toBlob(resolve, 'image/png', 0.9);
            });

            // Restore share buttons
            shareButtons.forEach((button, index) => {
                button.style.display = originalDisplayStates[index] || '';
            });
            
            // Restore share button state
            shareButton.innerHTML = originalContent;
            shareButton.disabled = false;

            // Create share data
            const shareData = this.createShareData(tileType, tileTitle, blob);

            // Try native sharing or fallback to download
            if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
                await navigator.share(shareData);
            } else {
                this.downloadImage(blob, tileTitle);
                this.showShareSuccessMessage(tileType);
            }

        } catch (error) {
            console.error('Error sharing tile:', error);
            this.restoreShareButton(tileType);
            Toast.error('Error sharing tile. Please try again.');
        }
    }

    /**
     * Load html2canvas if not already loaded
     */
    static async loadHtml2Canvas() {
        if (window.html2canvas) {
            return window.html2canvas;
        }
        
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
            script.onload = () => resolve(window.html2canvas);
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Add logo watermark to canvas
     */
    static async addLogoWatermark(tileCanvas) {
        const finalCanvas = document.createElement('canvas');
        const finalCtx = finalCanvas.getContext('2d');
        
        const padding = 30;
        finalCanvas.width = tileCanvas.width + (padding * 2);
        finalCanvas.height = tileCanvas.height + (padding * 2);
        
        // Fill background
        const gradient = finalCtx.createLinearGradient(0, 0, 0, finalCanvas.height);
        gradient.addColorStop(0, '#fafbfc');
        gradient.addColorStop(1, '#ffffff');
        finalCtx.fillStyle = gradient;
        finalCtx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);
        
        // Add shadow
        finalCtx.shadowColor = 'rgba(0, 0, 0, 0.08)';
        finalCtx.shadowBlur = 15;
        finalCtx.shadowOffsetX = 0;
        finalCtx.shadowOffsetY = 8;
        
        // Draw tile
        finalCtx.drawImage(tileCanvas, padding, padding);
        
        // Reset shadow
        finalCtx.shadowColor = 'transparent';
        finalCtx.shadowBlur = 0;
        
        // Add Ki Wellness watermark
        try {
            // Load the leaf logo
            const leafLogo = new Image();
            leafLogo.crossOrigin = 'anonymous';
            
            await new Promise((resolve, reject) => {
                leafLogo.onload = resolve;
                leafLogo.onerror = reject;
                leafLogo.src = '/static/public/branding/logo.png'; // Leaf logo
            });

            // Calculate watermark dimensions
            const watermarkWidth = Math.min(120, finalCanvas.width * 0.25);
            const watermarkHeight = (watermarkWidth * leafLogo.height) / leafLogo.width;
            
            // Position watermark in bottom-right corner with some padding
            const watermarkX = finalCanvas.width - watermarkWidth - 20;
            const watermarkY = finalCanvas.height - watermarkHeight - 20;
            
            // Add semi-transparent background for watermark
            finalCtx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            finalCtx.fillRect(watermarkX - 15, watermarkY - 15, watermarkWidth + 30, watermarkHeight + 30);
            
            // Add subtle border
            finalCtx.strokeStyle = 'rgba(16, 185, 129, 0.2)';
            finalCtx.lineWidth = 1;
            finalCtx.strokeRect(watermarkX - 15, watermarkY - 15, watermarkWidth + 30, watermarkHeight + 30);
            
            // Draw leaf logo
            finalCtx.drawImage(leafLogo, watermarkX, watermarkY, watermarkWidth, watermarkHeight);
            
            // Add "Ki Wellness" text in Quicksand font
            finalCtx.font = 'bold 16px "Quicksand", sans-serif';
            finalCtx.fillStyle = '#10b981'; // Forest green color
            finalCtx.textAlign = 'center';
            finalCtx.textBaseline = 'top';
            
            // Position text below the logo
            const textX = watermarkX + (watermarkWidth / 2);
            const textY = watermarkY + watermarkHeight + 5;
            
            // Add text shadow for better readability
            finalCtx.shadowColor = 'rgba(255, 255, 255, 0.8)';
            finalCtx.shadowBlur = 2;
            finalCtx.shadowOffsetX = 0;
            finalCtx.shadowOffsetY = 1;
            
            finalCtx.fillText('Ki Wellness', textX, textY);
            
            // Reset shadow
            finalCtx.shadowColor = 'transparent';
            finalCtx.shadowBlur = 0;
            
        } catch (error) {
            console.warn('Could not load logo for watermark:', error);
            
            // Fallback: Add text-only watermark
            finalCtx.font = 'bold 18px "Quicksand", sans-serif';
            finalCtx.fillStyle = 'rgba(16, 185, 129, 0.7)';
            finalCtx.textAlign = 'right';
            finalCtx.textBaseline = 'bottom';
            
            const textX = finalCanvas.width - 20;
            const textY = finalCanvas.height - 20;
            
            finalCtx.fillText('Ki Wellness', textX, textY);
        }

        return finalCanvas;
    }

    /**
     * Create share data
     */
    static createShareData(tileType, tileTitle, blob) {
        let shareTitle, shareText;
        
        switch(tileType) {
            case 'water':
                shareTitle = `Hydration Progress - Ki Wellness, Self Health Simplified`;
                shareText = `Staying hydrated with ${document.getElementById('waterAmount').textContent} oz of water today! 💧 Track your wellness journey with Ki Wellness, Self Health Simplified.`;
                break;
            case 'macros':
                shareTitle = `Nutrition Balance - Ki Wellness, Self Health Simplified`;
                shareText = `Fueling my body with ${document.getElementById('totalCalories').textContent} calories - balanced macros for optimal health! 🥗 Discover your nutrition insights with Ki Wellness, Self Health Simplified.`;
                break;
            case 'mood':
                const moodEmoji = document.getElementById('moodEmoji').textContent;
                const moodText = document.getElementById('moodText').textContent;
                shareTitle = `Wellness Check-in - Ki Wellness, Self Health Simplified`;
                shareText = `Today's wellness check: ${moodText} ${moodEmoji} Prioritizing mental health and mindfulness with Ki Wellness, Self Health Simplified.`;
                break;
            default:
                shareTitle = `${tileTitle} - Ki Wellness, Self Health Simplified`;
                shareText = `Check out my ${tileTitle.toLowerCase()} from Ki Wellness, Self Health Simplified!`;
        }

        return {
            title: shareTitle,
            text: shareText,
            url: 'https://kiwellness.org',
            files: [new File([blob], `${tileTitle.toLowerCase().replace(/\s+/g, '-')}.png`, { type: 'image/png' })]
        };
    }

    /**
     * Download image
     */
    static downloadImage(blob, tileTitle) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${tileTitle.toLowerCase().replace(/\s+/g, '-')}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Show share success message
     */
    static showShareSuccessMessage(tileType) {
        let successMessage;
        switch(tileType) {
            case 'water':
                successMessage = `💧 Hydration progress screenshot saved with Ki Wellness branding! Share your wellness journey with the link: https://kiwellness.org\n\n"Ki Wellness, Self Health Simplified"`;
                break;
            case 'macros':
                successMessage = `🥗 Nutrition balance screenshot saved with Ki Wellness branding! Share your health insights with the link: https://kiwellness.org\n\n"Ki Wellness, Self Health Simplified"`;
                break;
            case 'mood':
                successMessage = `😊 Wellness check-in screenshot saved with Ki Wellness branding! Share your mindfulness journey with the link: https://kiwellness.org\n\n"Ki Wellness, Self Health Simplified"`;
                break;
            default:
                successMessage = `Screenshot saved with Ki Wellness branding! Share it with the link: https://kiwellness.org\n\n"Ki Wellness, Self Health Simplified"`;
        }
        Toast.success(successMessage);
    }

    /**
     * Restore share button
     */
    static restoreShareButton(tileType) {
        const shareButton = document.querySelector(`[data-tile="${tileType}"]`);
        if (shareButton) {
            shareButton.disabled = false;
        }
    }
}

// Export classes for use in other modules
window.SessionManager = SessionManager;
window.ChartManager = ChartManager;
window.ModalManager = ModalManager;
window.LoadingManager = LoadingManager;
window.APIService = APIService;
window.DashboardUtils = DashboardUtils;
window.ShareManager = ShareManager;
