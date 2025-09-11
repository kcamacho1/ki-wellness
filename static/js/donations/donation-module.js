/**
 * Donation Module for Ki Wellness
 * Handles donation functionality with direct Stripe links
 */

class DonationModule {
    constructor() {
        this.donationUrl = "https://donate.stripe.com/7sYdR95ld0R9byt8VU3Je02";
        this.isInitialized = true;
        console.log('✅ Donation module initialized with direct Stripe link');
    }

    // Redirect to Stripe donation page
    redirectToDonation() {
        window.open(this.donationUrl, '_blank', 'noopener,noreferrer');
    }

    // Log donation events for analytics
    async logDonationEvent(eventType, eventData = {}) {
        try {
            await fetch('/api/log-donation-event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_type: eventType,
                    event_data: eventData
                })
            });
        } catch (error) {
            console.error('Error logging donation event:', error);
        }
    }

    // Public methods for external use
    donate() {
        this.redirectToDonation();
        this.logDonationEvent('donation_clicked', { source: 'button' });
    }

    getDonationUrl() {
        return this.donationUrl;
    }

    isEnabled() {
        return this.isInitialized;
    }
}

// Global donation module instance
window.donationModule = new DonationModule();

// Convenience functions for global access
window.openDonationModal = () => window.donationModule.donate();
window.closeDonationModal = () => {}; // No-op since we don't use modals
window.processDonation = () => window.donationModule.donate();
window.processModalDonation = () => window.donationModule.donate();
