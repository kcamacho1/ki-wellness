#!/bin/bash

# Setup weekly cron job for Ki Wellness AI analysis
# This script sets up a cron job to run every Monday at midnight (00:00)
# The analysis will look at the past 7 days of user data and generate fresh insights

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the cron job entry
CRON_JOB="0 0 * * 1 cd $SCRIPT_DIR && python scheduled_analysis.py >> logs/scheduled_analysis.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "scheduled_analysis.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "scheduled_analysis.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Create logs directory if it doesn't exist
mkdir -p logs

echo "✅ Weekly analysis cron job set up successfully!"
echo "📅 Analysis will run every Monday at midnight (00:00)"
echo "🔄 Each analysis covers the past 7 days of user data"
echo "📁 Logs will be saved to: $SCRIPT_DIR/logs/scheduled_analysis.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove this cron job: crontab -e"
