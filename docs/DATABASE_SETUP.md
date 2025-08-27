# Database Setup Guide

## Overview

This application uses a hybrid database approach:
- **Development**: SQLite (local file-based database)
- **Production**: PostgreSQL (cloud database)

## Development Setup

### Prerequisites
- Python 3.11+
- No PostgreSQL installation required

### Installation
```bash
# Install development dependencies (SQLite only)
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env file as needed

# Initialize the database
python scripts/init_database.py
```

### Running the Application
```bash
# Start Flask development server
python app.py

# Or use Flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

## Production Setup

### Prerequisites
- PostgreSQL database (e.g., Render.com, Heroku, AWS RDS)
- Environment variable `DATABASE_URL` set

### Installation
```bash
# Install all dependencies (including PostgreSQL)
pip install -r requirements.txt
```

### Environment Variables
```bash
# Required for production
DATABASE_URL=postgresql://username:password@host:port/database_name
SECRET_KEY=your-secret-key-here

# Optional
FLASK_ENV=production
```

## Database Configuration

The application automatically detects the environment:

### Development Mode
- **Trigger**: No `DATABASE_URL` environment variable
- **Database**: SQLite (`ki_wellness.db` file)
- **Console Output**: `🛠️ Running in DEVELOPMENT mode with SQLite`

### Production Mode
- **Trigger**: `DATABASE_URL` environment variable present
- **Database**: PostgreSQL (from `DATABASE_URL`)
- **Console Output**: `🚀 Running in PRODUCTION mode with PostgreSQL`

## Migration Between Environments

### Development to Production
1. Set up PostgreSQL database
2. Set `DATABASE_URL` environment variable
3. Run database migrations
4. Deploy application

### Production to Development
1. Remove `DATABASE_URL` environment variable
2. Application will automatically use SQLite
3. Database file will be created locally

## Troubleshooting

### PostgreSQL Connection Issues
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
- Check network connectivity to database
- Ensure database exists and user has proper permissions

### SQLite Issues
- Ensure write permissions in application directory
- Check available disk space
- Verify Python has SQLite support (usually included by default)

## Benefits of This Approach

### Development
- ✅ No database setup required
- ✅ Fast startup and development
- ✅ Portable (database file travels with code)
- ✅ No external dependencies

### Production
- ✅ Scalable PostgreSQL database
- ✅ ACID compliance
- ✅ Concurrent user support
- ✅ Backup and recovery options
