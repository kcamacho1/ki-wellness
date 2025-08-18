class AICoachManager {
    constructor() {
        this.userData = null;
        this.analysis = null;
        this.chatHistory = [];
        this.init();
    }

    async init() {
        // Load stored analysis first (fast)
        await this.loadStoredAnalysis();
        
        // Load user data in background
        this.loadUserData();
        
        this.setupEventListeners();
        this.showMainContent();
    }

    async warmupModel() {
        try {
            console.log('Warming up AI model...');
            await fetch('/api/warmup-ollama');
            console.log('Model warmed up successfully');
        } catch (error) {
            console.log('Model warmup failed, continuing anyway:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('refresh-analysis').addEventListener('click', () => this.refreshAnalysis());
        
        // Chat modal controls
        document.getElementById('chat-button').addEventListener('click', () => this.openChat());
        document.getElementById('close-chat').addEventListener('click', () => this.closeChat());
        
        // Chat functionality
        document.getElementById('send-message').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Quick question buttons
        document.querySelectorAll('.quick-question').forEach(button => {
            button.addEventListener('click', () => {
                const question = button.textContent;
                document.getElementById('chat-input').value = question;
                this.sendMessage();
            });
        });
    }

    openChat() {
        document.getElementById('chat-modal').classList.remove('hidden');
        document.getElementById('chat-input').focus();
    }

    closeChat() {
        document.getElementById('chat-modal').classList.add('hidden');
    }

    async loadUserData() {
        try {
            // Get last 30 days of data for analysis
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 30);

            const response = await fetch(`/api/user-data-for-analysis?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`);
            const data = await response.json();
            
            if (data.success) {
                this.userData = data.data;
                // If there are no logs at all, show CTA immediately
                if (!this.hasAnyLogs()) {
                    this.displayNoLogsCTA();
                }
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    async loadStoredAnalysis() {
        try {
            const response = await fetch('/api/get-stored-analysis');
            const data = await response.json();
            
            if (data.success) {
                this.analysis = data.analysis;
                this.displayAnalysis();
                
                // Show last updated time if available
                if (data.updated_at) {
                    const updatedDate = new Date(data.updated_at);
                    this.displayLastUpdated(updatedDate);
                    
                    const daysAgo = Math.floor((new Date() - updatedDate) / (1000 * 60 * 60 * 24));
                    console.log(`Analysis last updated ${daysAgo} days ago`);
                }
            } else {
                this.showFallbackAnalysis();
            }
        } catch (error) {
            console.error('Error loading stored analysis:', error);
            this.showFallbackAnalysis();
        }
    }

    displayLastUpdated(updatedDate) {
        const now = new Date();
        const timeDiff = now - updatedDate;
        const daysDiff = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
        const hoursDiff = Math.floor(timeDiff / (1000 * 60 * 60));
        
        let timeText = '';
        if (daysDiff > 0) {
            timeText = `${daysDiff} day${daysDiff > 1 ? 's' : ''} ago`;
        } else if (hoursDiff > 0) {
            timeText = `${hoursDiff} hour${hoursDiff > 1 ? 's' : ''} ago`;
        } else {
            timeText = 'Just now';
        }
        
        // Update the last updated text in the UI
        const lastUpdatedElement = document.getElementById('last-updated');
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = `Last updated: ${timeText}`;
            lastUpdatedElement.style.display = 'block';
        }
    }

    async generateAnalysis() {
        try {
            // Add timeout to prevent hanging - increased to 60 seconds for comprehensive analysis
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
            
            console.log('Generating AI analysis with comprehensive data...');
            
            const response = await fetch('/api/generate-ai-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_data: this.userData
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const data = await response.json();
            
            if (data.success) {
                this.analysis = data.analysis;
                this.displayAnalysis();
                console.log('Analysis generated successfully');
            } else {
                console.error('Analysis error:', data.error);
                this.showFallbackAnalysis();
            }
        } catch (error) {
            console.error('Error generating analysis:', error);
            
            // Check if it's a timeout error
            if (error.name === 'AbortError') {
                console.log('Analysis timed out - showing fallback');
                this.showTimeoutMessage();
            } else {
                this.showFallbackAnalysis();
            }
        }
    }

    showTimeoutMessage() {
        this.analysis = {
            patterns: [
                {"title": "Analysis in Progress", "description": "Your comprehensive analysis is taking longer than expected. This usually means you have a lot of data to analyze! Try refreshing in a moment or check back later."}
            ],
            suggestions: [
                {"title": "Try Again", "description": "The AI is processing your detailed wellness data. You can try refreshing the analysis again, or continue using the app while it processes in the background."}
            ]
        };
        this.displayAnalysis();
    }

    showFallbackAnalysis() {
        // If the user has no logs, prioritize CTA over generic fallback
        if (!this.hasAnyLogs()) {
            this.displayNoLogsCTA();
            return;
        }
        this.analysis = {
            patterns: [
                {"title": "Getting Started", "description": "Welcome to your AI Health Coach! Start logging your food, water, and mood to get personalized insights."}
            ],
            suggestions: [
                {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
            ]
        };
        this.displayAnalysis();
    }

    // Returns true if there is at least one log entry across food, water, or mood
    hasAnyLogs() {
        if (!this.userData) return false;
        const foodCount = Array.isArray(this.userData.food_logs) ? this.userData.food_logs.length : 0;
        const waterCount = Array.isArray(this.userData.water_logs) ? this.userData.water_logs.length : 0;
        const moodCount = Array.isArray(this.userData.mood_logs) ? this.userData.mood_logs.length : 0;
        return (foodCount + waterCount + moodCount) > 0;
    }

    // Renders a clear call-to-action prompting the user to log entries
    displayNoLogsCTA() {
        const patterns = document.getElementById('patterns-content');
        const suggestions = document.getElementById('suggestions-content');
        const ctaHtml = `
            <div class="bg-white border border-gray-200 rounded-xl p-6 text-center">
                <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-ki-green-50 flex items-center justify-center">
                    <svg class="w-6 h-6 text-ki-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                </div>
                <h4 class="text-lg font-semibold text-gray-900">Start your wellness journey</h4>
                <p class="text-sm text-gray-600 mt-1">Log your first food, water, or mood entry to unlock personalized insights.</p>
                <a href="/dashboard" class="inline-block mt-4 px-4 py-2 bg-ki-green-600 text-white text-sm font-medium rounded-lg hover:bg-ki-green-700 transition-colors">Go to Dashboard</a>
            </div>
        `;
        if (patterns) patterns.innerHTML = ctaHtml;
        if (suggestions) suggestions.innerHTML = ctaHtml;
    }

    displayAnalysis() {
        // If no logs, show CTA instead of analysis
        if (!this.hasAnyLogs()) {
            this.displayNoLogsCTA();
            return;
        }
        this.displayPatterns();
        this.displaySuggestions();
    }

    displayPatterns() {
        const container = document.getElementById('patterns-content');
        
        if (!this.analysis.patterns || this.analysis.patterns.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>Not enough data to identify patterns yet. Keep logging for personalized insights!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.analysis.patterns.map(pattern => `
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div class="flex items-start space-x-3">
                    <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg class="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 mb-1">${pattern.title}</h4>
                        <p class="text-sm text-gray-600">${pattern.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    displaySuggestions() {
        const container = document.getElementById('suggestions-content');
        
        if (!this.analysis.suggestions || this.analysis.suggestions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>Complete your profile goals to get personalized suggestions!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.analysis.suggestions.map(suggestion => `
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div class="flex items-start space-x-3">
                    <div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg class="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 mb-1">${suggestion.title}</h4>
                        <p class="text-sm text-gray-600">${suggestion.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessageToChat('user', message);
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            console.log('Sending message to AI:', message);
            console.log('User data:', this.userData);
            console.log('Analysis:', this.analysis);
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
            
            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_data: this.userData,
                    analysis: this.analysis,
                    chat_history: this.chatHistory
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (data.success) {
                this.addMessageToChat('assistant', data.response);
                this.chatHistory.push({ role: 'user', content: message });
                this.chatHistory.push({ role: 'assistant', content: data.response });
            } else {
                const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
                this.addMessageToChat('assistant', errorMsg);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessageToChat('assistant', 'Network error. Please check your connection and try again.');
        }
    }

    addMessageToChat(role, content) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="flex-1"></div>
                <div class="bg-ki-green-600 text-white rounded-lg p-3 max-w-xs lg:max-w-md">
                    <p class="text-sm">${content}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-ki-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                    </svg>
                </div>
                <div class="bg-white rounded-lg p-3 shadow-sm max-w-xs lg:max-w-md">
                    <p class="text-sm text-gray-800">${content}</p>
                </div>
            `;
        }
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    showTypingIndicator() {
        const container = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 bg-ki-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        `;
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async refreshAnalysis() {
        // Show loading state with progress message
        document.getElementById('loading-state').classList.remove('hidden');
        document.getElementById('main-content').classList.add('hidden');
        
        // Update loading message to show progress
        const loadingText = document.querySelector('#loading-state p');
        if (loadingText) {
            loadingText.textContent = 'Loading your wellness data...';
        }
        
        try {
            // Load fresh user data first
            await this.loadUserData();
            
            // Update loading message
            if (loadingText) {
                loadingText.textContent = 'Analyzing your patterns and trends...';
            }
            
            // Generate new analysis with comprehensive data
            await this.generateAnalysis();
            
            // Update the last updated display
            this.displayLastUpdated(new Date());
            
            // Show success message briefly
            this.showRefreshSuccess();
        } catch (error) {
            console.error('Error refreshing analysis:', error);
            // Show error message
            this.showRefreshError();
        } finally {
            // Hide loading state
            document.getElementById('loading-state').classList.add('hidden');
            document.getElementById('main-content').classList.remove('hidden');
        }
    }

    showRefreshSuccess() {
        // Show a brief success message
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        successDiv.textContent = 'Analysis refreshed successfully!';
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    showRefreshError() {
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        errorDiv.textContent = 'Failed to refresh analysis. Please try again.';
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    showMainContent() {
        document.getElementById('loading-state').classList.add('hidden');
        document.getElementById('main-content').classList.remove('hidden');
    }
}

// Initialize the AI Coach manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AICoachManager();
});
