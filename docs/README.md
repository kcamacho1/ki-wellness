# 📚 Documentation

This directory contains documentation for the KI Wellness application.

## 📁 Structure

```
docs/
├── README.md           # This file - documentation overview
└── private/           # 🔒 Private documentation (not in version control)
    ├── README.md      # Private docs explanation
    ├── ADMIN_ACCOUNT_SETUP.md    # Admin account setup (sensitive)
    └── SECURITY_REVIEW.md        # Security review (sensitive)
```

## 🔒 Private Documentation

The `private/` directory contains sensitive documentation that is **NOT** committed to version control. This includes:

- Admin account setup and configuration
- Security reviews and assessments
- Internal system details
- Sensitive operational procedures

### Accessing Private Documentation

Private documentation is stored locally and should be:
- Accessed only by authorized personnel
- Not shared publicly
- Protected from unauthorized access
- Used for internal reference only

## 📝 Public Documentation

Public documentation is stored in the root directory and includes:

- `USERNAME_VALIDATION.md` - Username validation implementation
- `DEPENDENCY_REVIEW.md` - Dependency analysis and review
- `VENV_SETUP.md` - Virtual environment setup
- `RECAPTCHA_SETUP.md` - reCAPTCHA configuration
- `README.md` - Main project documentation

## 🔐 Security

- Private documentation is excluded from version control via `.gitignore`
- Sensitive information is stored securely
- Access control is maintained for private docs
- Security best practices are followed

## 📋 Usage

1. **Public docs**: Available to all project contributors
2. **Private docs**: Internal use only, not in version control
3. **Security**: Follow security guidelines for sensitive information
4. **Maintenance**: Keep documentation updated and secure
