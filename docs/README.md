# Ki Wellness Documentation

This directory contains all documentation for the Ki Wellness application.

## Directory Structure

### `/setup/` - Setup and Configuration Guides
- **RECAPTCHA_SETUP.md** - Google reCAPTCHA v3 integration setup
- **STRIPE_SETUP.md** - Stripe payment integration setup
- **VENV_SETUP.md** - Virtual environment setup guide

### `/development/` - Development and Debugging Documentation
- **CLEANUP_SUMMARY.md** - Summary of codebase cleanup activities
- **DATABASE_CLEANUP_SUMMARY.md** - Database cleanup and migration summary
- **DATABASE_CONFIG.md** - Database configuration and setup
- **DEPENDENCY_REVIEW.md** - Python dependencies review and management
- **TURNSTILE_DEBUG_SUMMARY.md** - Cloudflare Turnstile debugging (legacy)
- **USERNAME_VALIDATION.md** - Username validation rules and implementation

### `/private/` - Private Documentation (Gitignored)
- **ADMIN_ACCOUNT_SETUP.md** - Admin account setup procedures
- **SECURITY_REVIEW.md** - Security audit and review documentation
- **README.md** - Private documentation index

## Quick Links

### For New Developers
1. Start with `/setup/VENV_SETUP.md` for environment setup
2. Review `/setup/STRIPE_SETUP.md` for payment integration
3. Check `/setup/RECAPTCHA_SETUP.md` for security setup

### For Database Management
1. Review `/development/DATABASE_CONFIG.md` for configuration
2. Check `/development/DATABASE_CLEANUP_SUMMARY.md` for recent changes
3. See `/development/CLEANUP_SUMMARY.md` for overall cleanup status

### For Troubleshooting
1. Check `/development/TURNSTILE_DEBUG_SUMMARY.md` for security issues
2. Review `/development/USERNAME_VALIDATION.md` for validation problems
3. See `/development/DEPENDENCY_REVIEW.md` for dependency issues

## Contributing

When adding new documentation:
- Place setup guides in `/setup/`
- Place development/debugging docs in `/development/`
- Place sensitive information in `/private/`
- Update this README.md to reflect changes
