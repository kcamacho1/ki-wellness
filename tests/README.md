# Ki Wellness Test Suite

This directory contains all test files for the Ki Wellness application.

## Test Files

### `test_admin_tabs.py`
- **Purpose**: Tests admin dashboard tab functionality
- **Tests**: Verifies all tab content divs, buttons, and JavaScript functions are present
- **Usage**: `python tests/test_admin_tabs.py`

### `test_admin_flexible_tier.py`
- **Purpose**: Tests admin flexible tier functionality
- **Tests**: Verifies flexible tier settings and configurations
- **Usage**: `python tests/test_admin_flexible_tier.py`

### `test_recaptcha_debug.py`
- **Purpose**: Tests reCAPTCHA integration and debugging
- **Tests**: Verifies reCAPTCHA functionality and error handling
- **Usage**: `python tests/test_recaptcha_debug.py`

### `test_turnstile_debug.py`
- **Purpose**: Tests Cloudflare Turnstile integration (legacy)
- **Tests**: Verifies Turnstile functionality and error handling
- **Usage**: `python tests/test_turnstile_debug.py`

### `test_username_validation.py`
- **Purpose**: Tests username validation functionality
- **Tests**: Verifies username validation rules and constraints
- **Usage**: `python tests/test_username_validation.py`

## Running Tests

To run all tests from the project root:

```bash
# Run individual tests
python tests/test_admin_tabs.py
python tests/test_admin_flexible_tier.py
python tests/test_recaptcha_debug.py
python tests/test_turnstile_debug.py
python tests/test_username_validation.py

# Or run all tests (if you have a test runner)
python -m pytest tests/
```

## Test Environment

Make sure you have the following set up before running tests:
- Python 3.8+
- Required dependencies installed (`pip install -r requirements.txt`)
- Environment variables configured (see `.env.example`)
- Database properly configured
