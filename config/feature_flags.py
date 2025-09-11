"""
Feature flags configuration for Ki Wellness
Allows enabling/disabling individual pages and features without affecting others
"""
import os
from typing import Dict, Any

class FeatureFlags:
    """Feature flags manager for controlling page availability"""
    
    def __init__(self):
        self.flags = {
            # Core pages - always enabled
            'auth': True,
            'dashboard': True,
            'profile': True,
            
            # Optional features - can be disabled
            'recipes': self._get_flag('FEATURE_RECIPES', True),
            'ai_coach': self._get_flag('FEATURE_AI_COACH', True),
            'admin': self._get_flag('FEATURE_ADMIN', True),
            'payments': self._get_flag('FEATURE_PAYMENTS', True),
            'donations': self._get_flag('FEATURE_DONATIONS', True),
            'barcode_scanner': self._get_flag('FEATURE_BARCODE_SCANNER', True),
            'nutrition_review': self._get_flag('FEATURE_NUTRITION_REVIEW', True),
            'analytics': self._get_flag('FEATURE_ANALYTICS', True),
            
            # Static pages
            'static_pages': True,
            'support': self._get_flag('FEATURE_SUPPORT', True),
            'human_help': self._get_flag('FEATURE_HUMAN_HELP', True),
        }
    
    def _get_flag(self, env_var: str, default: bool) -> bool:
        """Get feature flag from environment variable"""
        value = os.getenv(env_var, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.flags.get(feature, False)
    
    def get_disabled_features(self) -> list:
        """Get list of disabled features"""
        return [feature for feature, enabled in self.flags.items() if not enabled]
    
    def get_enabled_features(self) -> list:
        """Get list of enabled features"""
        return [feature for feature, enabled in self.flags.items() if enabled]
    
    def get_status(self) -> Dict[str, bool]:
        """Get all feature flags status"""
        return self.flags.copy()
    
    def disable_feature(self, feature: str) -> bool:
        """Disable a feature at runtime"""
        if feature in self.flags:
            self.flags[feature] = False
            return True
        return False
    
    def enable_feature(self, feature: str) -> bool:
        """Enable a feature at runtime"""
        if feature in self.flags:
            self.flags[feature] = True
            return True
        return False

# Global feature flags instance
feature_flags = FeatureFlags()

def is_feature_enabled(feature: str) -> bool:
    """Convenience function to check if a feature is enabled"""
    return feature_flags.is_enabled(feature)

def get_feature_status() -> Dict[str, bool]:
    """Get all feature flags status"""
    return feature_flags.get_status()
