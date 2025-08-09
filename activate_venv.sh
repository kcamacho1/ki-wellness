#!/bin/bash
# Activate the virtual environment for KI Wellness

echo "🚀 Activating KI Wellness virtual environment..."
source venv/bin/activate

if [ $? -eq 0 ]; then
    echo "✅ Virtual environment activated successfully!"
    echo "📦 Python version: $(python --version)"
    echo "🔧 Flask version: $(python -c "import flask; print(flask.__version__)" 2>/dev/null || echo "Not installed")"
    echo ""
    echo "💡 To deactivate, run: deactivate"
    echo "💡 To run the application: python run.py"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi
