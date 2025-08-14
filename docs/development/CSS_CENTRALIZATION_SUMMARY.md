# CSS Centralization Summary

## Overview
Successfully centralized all repeated CSS styling across the Ki Wellness application into a single global stylesheet, improving maintainability and consistency.

## Changes Made

### 1. Created Global Stylesheet
- **File**: `app/static/css/ki-wellness-global.css`
- **Purpose**: Central repository for all common styles used across the application
- **Features**:
  - Quicksand font family import and global application
  - Custom color variables (forest-green, mint-green, etc.)
  - Common gradients (hero-gradient, ai-gradient, etc.)
  - Reusable animations (float, pulse-glow, etc.)
  - Card component styles (feature-card, coaching-card, etc.)
  - Button styles with consistent theming
  - Form input styles
  - Utility classes for shadows, transitions, etc.
  - Responsive utilities
  - Accessibility features

### 2. Updated HTML Templates
Replaced inline `<style>` blocks with global stylesheet links in the following files:

#### Main Pages
- `app/templates/landing.html` - Removed gradient and animation styles
- `app/templates/coaching.html` - Removed gradient and story-card styles
- `app/templates/ai_coaching.html` - Removed feature-card and gradient styles
- `app/templates/coaching_selection.html` - Removed coaching-card and gradient styles
- `app/templates/ai_self_health.html` - Removed feature-card and gradient styles

#### Authentication Pages
- `app/templates/login.html` - Removed button and color styles, kept hero-gradient
- `app/templates/register.html` - Removed button and color styles, kept hero-gradient
- `app/templates/forgot_password.html` - Removed button styles
- `app/templates/reset_password.html` - Removed button styles

#### Dashboard & User Pages
- `app/templates/dashboard.html` - Added global stylesheet, kept dashboard-specific styles
- `app/templates/reviews.html` - Removed review-card styles, kept star-rating styles
- `app/templates/onboarding.html` - Removed step-indicator styles, kept onboarding-specific styles
- `app/templates/settings.html` - Removed color utility styles
- `app/templates/reminders.html` - Removed reminder-card styles, kept notification-toggle styles

### 3. Preserved Page-Specific Styles
Some pages retained their specific styles where they were unique to that page:
- **Reviews page**: Star rating styles (`.star-rating`, `.star`)
- **Dashboard**: Analysis content and patterns styling
- **Onboarding**: Step indicator animations
- **Reminders**: Notification toggle styles
- **Login/Register**: Hero gradient (unique to auth pages)

### 4. Font Standardization
- **Global font**: Quicksand (as requested by user)
- **Implementation**: Added Google Fonts import in global stylesheet
- **Fallback**: Comprehensive fallback font stack for better compatibility

## Benefits Achieved

### 1. Maintainability
- Single source of truth for common styles
- Easier to update brand colors and animations
- Reduced code duplication

### 2. Consistency
- Uniform styling across all pages
- Standardized color palette
- Consistent animations and transitions

### 3. Performance
- Reduced CSS file sizes on individual pages
- Better browser caching of styles
- Faster page loads

### 4. Developer Experience
- Easier to find and modify styles
- Clear separation between global and page-specific styles
- Better organization of CSS rules

## File Structure
```
app/static/css/
└── ki-wellness-global.css    # Global stylesheet

app/templates/
├── landing.html              # Uses global styles
├── coaching.html             # Uses global styles
├── ai_coaching.html          # Uses global styles
├── coaching_selection.html   # Uses global styles
├── ai_self_health.html       # Uses global styles
├── login.html                # Uses global styles + hero-gradient
├── register.html             # Uses global styles + hero-gradient
├── forgot_password.html      # Uses global styles
├── reset_password.html       # Uses global styles
├── dashboard.html            # Uses global styles + dashboard-specific
├── reviews.html              # Uses global styles + star-rating
├── onboarding.html           # Uses global styles + step-indicator
├── settings.html             # Uses global styles
└── reminders.html            # Uses global styles + notification-toggle
```

## Next Steps
1. Consider creating additional component-specific stylesheets for complex components
2. Implement CSS minification for production
3. Add CSS linting rules to maintain consistency
4. Consider using CSS custom properties for dynamic theming

## Notes
- All pages now use the Quicksand font family as the primary font
- Color variables are defined in CSS custom properties for easy theming
- Animations are standardized and reusable
- Button styles are consistent across all forms
- Card components have uniform hover effects and transitions
