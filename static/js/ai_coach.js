class AICoachManager {
    constructor() {
        this.userData = null;
        this.analysis = null;
        this.chatHistory = [];
        this.userSummary = null;
        this.contextCache = new Map();
        this.init();
    }

    async init() {
        // Load stored analysis first (fast)
        await this.loadStoredAnalysis();
        
        // Load minimal user summary in background
        this.loadUserSummary();
        
        // Check premium status
        await this.checkPremiumStatus();
        
        this.setupEventListeners();
        this.showMainContent();
    }

    async warmupModel() {
        try {
            console.log('Warming up AI model...');
            await fetch('/api/warmup-openrouter');
            console.log('Model warmed up successfully');
        } catch (error) {
            console.log('Model warmup failed, continuing anyway:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('refresh-analysis').addEventListener('click', () => this.refreshAnalysis());
        
        // Chat modal controls
        document.getElementById('chat-button').addEventListener('click', () => this.openChat());
        document.getElementById('chat-button-hero').addEventListener('click', () => this.openChat());
        document.getElementById('close-chat').addEventListener('click', () => this.closeChat());
        
        // Chat resize functionality
        document.getElementById('resize-chat').addEventListener('click', () => this.toggleChatSize());
        
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
        // Check premium status before opening chat
        if (!this.isPremium) {
            this.showUpgradePrompt('AI Chat is a premium feature. Upgrade to chat with your personalized AI Health Coach!');
            return;
        }
        
        document.getElementById('chat-modal').classList.remove('hidden');
        document.getElementById('chat-input').focus();
    }

    closeChat() {
        document.getElementById('chat-modal').classList.add('hidden');
        // Reset chat size when closing
        this.resetChatSize();
    }

    toggleChatSize() {
        const container = document.getElementById('chat-container');
        const resizeIcon = document.getElementById('resize-icon');
        
        if (container.classList.contains('expanded')) {
            // Collapse to normal size
            container.classList.remove('expanded');
            container.classList.remove('w-[800px]', 'h-[700px]', 'bottom-6', 'right-6');
            container.classList.add('w-96', 'h-[600px]', 'bottom-6', 'right-6');
            resizeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>';
        } else {
            // Expand to larger size
            container.classList.add('expanded');
            container.classList.remove('w-96', 'h-[600px]');
            container.classList.add('w-[800px]', 'h-[700px]');
            resizeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4h16v16H4V4z"></path>';
        }
    }

    resetChatSize() {
        const container = document.getElementById('chat-container');
        const resizeIcon = document.getElementById('resize-icon');
        
        container.classList.remove('expanded', 'w-[800px]', 'h-[700px]');
        container.classList.add('w-96', 'h-[600px]');
        resizeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>';
    }

    async loadUserSummary() {
        try {
            console.log('Loading user summary...');
            const response = await fetch('/api/user-summary');
            const data = await response.json();
            
            if (data.success) {
                this.userSummary = data.summary;
                this.userData = data.summary; // Use summary as userData for chat
                console.log('User summary loaded:', this.userSummary);
                
                if (!this.hasAnyLogs()) {
                    this.displayNoLogsCTA();
                }
            } else {
                console.error('Failed to load user summary:', data.error);
            }
        } catch (error) {
            console.error('Error loading user summary:', error);
        }
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

                // If analysis exists, do not show CTA unless there are no logs in the last 7 days
                // We will compute that once userData is loaded
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

    // Returns true if there is at least one log entry across food, water, or mood (last 7 days by default)
    hasAnyLogs(daysWindow = 7) {
        if (!this.userData && !this.userSummary) return false;
        
        const data = this.userSummary || this.userData;
        if (!data) return false;
        
        const now = new Date();
        const isRecent = (iso) => {
            const d = new Date(iso);
            return (now - d) <= daysWindow * 24 * 60 * 60 * 1000;
        };
        
        // Check food logs
        const foodRecent = (data.food_logs || []).some(l => isRecent(l.date)) || 
                          (data.food_summary && data.food_summary.total_entries > 0);
        
        // Check water logs
        const waterRecent = (data.water_logs || []).some(l => isRecent(l.date)) || 
                           (data.water_summary && data.water_summary.total_entries > 0);
        
        // Check mood logs
        const moodRecent = (data.mood_logs || []).some(l => isRecent(l.date)) || 
                          (data.mood_summary && data.mood_summary.total_entries > 0);
        
        return foodRecent || waterRecent || moodRecent;
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
        // Show CTA only if there are no logs in the last 7 days AND no saved analysis
        if (!this.hasAnyLogs(7) && (!this.analysis || (!this.analysis.patterns && !this.analysis.suggestions))) {
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
                        ${Array.isArray(suggestion.sources) && suggestion.sources.length > 0 ? `
                        <div class="mt-2 space-y-1">
                            ${suggestion.sources.slice(0,3).map(src => `
                                <a href="${src.url}" target="_blank" rel="noopener" class="inline-block text-xs text-blue-600 hover:underline">
                                    Source: ${src.title || src.url}
                                </a>
                            `).join('')}
                        </div>
                        ` : ''}
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
            // Determine what context is needed based on the message
            const contextType = this.determineContextType(message);
            const context = await this.getOptimizedContext(contextType, message);
            
            console.log('Sending message to AI:', message);
            console.log('Context type:', contextType);
            console.log('Context:', context);
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // Reduced to 10 seconds
            
            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    context: context,
                    context_type: contextType,
                    chat_history: this.chatHistory.slice(-5) // Only last 5 messages
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
                let responseText = data.response;
                
                // Add note if using fallback response
                if (data.note) {
                    responseText += `\n\n💡 *${data.note}*`;
                }
                
                this.addMessageToChat('assistant', responseText);
                this.chatHistory.push({ role: 'user', content: message });
                this.chatHistory.push({ role: 'assistant', content: data.response });
            } else {
                // Handle premium upgrade requirement
                if (data.requires_upgrade) {
                    this.showUpgradePrompt(data.message);
                } else {
                    const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
                    this.addMessageToChat('assistant', errorMsg);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            
            if (error.name === 'AbortError') {
                this.addMessageToChat('assistant', 'The request took too long. Please try asking a more specific question or try again in a moment.');
            } else {
                this.addMessageToChat('assistant', 'Network error. Please check your connection and try again.');
            }
        }
    }

    determineContextType(message) {
        const lowerMessage = message.toLowerCase();
        
        // Food-related questions
        if (lowerMessage.includes('food') || lowerMessage.includes('eat') || lowerMessage.includes('meal') || 
            lowerMessage.includes('calorie') || lowerMessage.includes('nutrition') || lowerMessage.includes('diet')) {
            return 'food';
        }
        
        // Mood-related questions
        if (lowerMessage.includes('mood') || lowerMessage.includes('feel') || lowerMessage.includes('emotion') || 
            lowerMessage.includes('happy') || lowerMessage.includes('sad') || lowerMessage.includes('stress')) {
            return 'mood';
        }
        
        // Water-related questions
        if (lowerMessage.includes('water') || lowerMessage.includes('hydrate') || lowerMessage.includes('drink') || 
            lowerMessage.includes('fluid')) {
            return 'water';
        }
        
        // General wellness questions
        if (lowerMessage.includes('pattern') || lowerMessage.includes('trend') || lowerMessage.includes('progress') || 
            lowerMessage.includes('analysis') || lowerMessage.includes('insight')) {
            return 'analysis';
        }
        
        // Default to minimal context
        return 'minimal';
    }

    async getOptimizedContext(contextType, message) {
        // Check cache first
        const cacheKey = `${contextType}_${this.userSummary?.profile?.id || 'default'}`;
        if (this.contextCache.has(cacheKey)) {
            console.log('Using cached context for:', contextType);
            return this.contextCache.get(cacheKey);
        }

        let context = {
            profile: this.userSummary?.profile || {},
            analysis: this.analysis || {},
            chat_history: this.chatHistory.slice(-3)
        };

        // Add specific data based on context type
        switch (contextType) {
            case 'food':
                context.food_summary = this.userSummary?.food_summary || {};
                break;
            case 'mood':
                context.mood_summary = this.userSummary?.mood_summary || {};
                break;
            case 'water':
                context.water_summary = this.userSummary?.water_summary || {};
                break;
            case 'analysis':
                context.recent_patterns = this.userSummary?.recent_patterns || [];
                break;
            case 'minimal':
            default:
                // Keep minimal context
                break;
        }

        // Cache the context
        this.contextCache.set(cacheKey, context);
        console.log('Cached context for:', contextType);
        return context;
    }

    addMessageToChat(role, content) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="flex-1"></div>
                <div class="bg-ki-green-600 text-white rounded-lg p-3 max-w-xs lg:max-w-md">
                    <p class="text-sm">${this.escapeHtml(content)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm overflow-hidden border border-gray-200">
                    <img src="/static/assets/branding/AI Health Coach.png" alt="AI Health Coach" class="w-full h-full object-cover">
                </div>
                <div class="bg-white rounded-lg p-3 shadow-sm max-w-xs lg:max-w-md">
                    <div class="text-sm text-gray-800 prose prose-sm max-w-none">
                        ${this.formatMessageContent(content)}
                    </div>
                </div>
            `;
        }
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
        
        // Make links clickable after adding to DOM
        if (role === 'assistant') {
            this.makeLinksClickable(messageDiv);
        }
    }

    formatMessageContent(content) {
        // Convert URLs to clickable links
        let formattedContent = content;
        
        // Handle links in the format [Link: Description]
        formattedContent = formattedContent.replace(
            /\[([^\]]+):\s*([^\]]+)\]/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline font-medium">$2</a>'
        );
        
        // Handle plain URLs
        formattedContent = formattedContent.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>'
        );
        
        // Handle emojis and special formatting
        formattedContent = formattedContent
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/📚/g, '<span class="text-purple-600">📚</span>')
            .replace(/💡/g, '<span class="text-yellow-600">💡</span>')
            .replace(/⚡/g, '<span class="text-orange-600">⚡</span>')
            .replace(/💧/g, '<span class="text-blue-600">💧</span>');
        
        return formattedContent;
    }

    makeLinksClickable(messageDiv) {
        const links = messageDiv.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const url = link.href;
                if (url && url !== '#') {
                    window.open(url, '_blank', 'noopener,noreferrer');
                }
            });
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showUpgradePrompt(message) {
        const upgradeMessage = `
            <div class="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div class="flex items-center space-x-3 mb-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <div>
                        <h3 class="font-semibold text-blue-900">Premium Feature</h3>
                        <p class="text-blue-700 text-sm">${message}</p>
                    </div>
                </div>
                <div class="flex space-x-3">
                    <button onclick="window.location.href='/profile'" 
                            class="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200">
                        💳 Upgrade Now
                    </button>
                    <button onclick="this.parentElement.parentElement.remove()" 
                            class="px-3 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300 transition-all duration-200">
                        Maybe Later
                    </button>
                </div>
            </div>
        `;
        
        this.addMessageToChat('assistant', upgradeMessage);
    }

    async checkPremiumStatus() {
        try {
            const response = await fetch('/api/subscription-status');
            const data = await response.json();
            
            if (data.success) {
                this.isPremium = data.is_premium;
                this.updateUIForPremiumStatus();
            } else {
                console.error('Failed to check premium status:', data.error);
                this.isPremium = false;
                this.updateUIForPremiumStatus();
            }
        } catch (error) {
            console.error('Error checking premium status:', error);
            this.isPremium = false;
            this.updateUIForPremiumStatus();
        }
    }

    updateUIForPremiumStatus() {
        const premiumPrompt = document.getElementById('premium-upgrade-prompt');
        const aiFeatures = document.getElementById('ai-features');
        const chatButton = document.getElementById('chat-button');
        const refreshPremiumBadge = document.getElementById('refresh-premium-badge');
        const chatPremiumBadge = document.getElementById('chat-premium-badge');
        const chatTooltipText = document.getElementById('chat-tooltip-text');
        const heroPremiumBadge = document.getElementById('hero-premium-badge');
        
        if (this.isPremium) {
            // Premium user - show AI features and enable chat
            if (premiumPrompt) premiumPrompt.classList.add('hidden');
            if (aiFeatures) aiFeatures.classList.remove('hidden');
            if (chatButton) {
                chatButton.classList.remove('hidden');
                chatButton.classList.remove('premium-locked');
            }
            if (refreshPremiumBadge) refreshPremiumBadge.classList.add('hidden');
            if (chatPremiumBadge) chatPremiumBadge.classList.add('hidden');
            if (heroPremiumBadge) heroPremiumBadge.classList.add('hidden');
            if (chatTooltipText) chatTooltipText.textContent = 'Chat with AI Coach';
        } else {
            // Free user - show upgrade prompt, but keep chat button visible with premium indicator
            if (premiumPrompt) premiumPrompt.classList.remove('hidden');
            if (aiFeatures) aiFeatures.classList.add('hidden');
            if (chatButton) {
                chatButton.classList.remove('hidden');
                chatButton.classList.add('premium-locked');
            }
            if (refreshPremiumBadge) refreshPremiumBadge.classList.remove('hidden');
            if (chatPremiumBadge) chatPremiumBadge.classList.remove('hidden');
            if (heroPremiumBadge) heroPremiumBadge.classList.remove('hidden');
            if (chatTooltipText) chatTooltipText.textContent = 'Upgrade to Chat with AI Coach';
        }
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
        // Check premium status before allowing refresh
        if (!this.isPremium) {
            this.showUpgradePrompt('Refresh Analysis is a premium feature. Upgrade to get fresh insights and updated recommendations.');
            return;
        }
        
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
