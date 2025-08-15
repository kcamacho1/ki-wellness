#!/bin/bash

# Ki Wellness - Database Auto-Fix Script
# ======================================
# This script provides easy access to the database auto-fix system
# It can check database status, apply fixes, and provide detailed reporting

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Function to show usage
show_usage() {
    echo "🔧 Ki Wellness - Database Auto-Fix Script"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  status     - Show current database status"
    echo "  check      - Check what needs to be fixed (dry run)"
    echo "  fix        - Apply database fixes automatically"
    echo "  fix-force  - Apply fixes without confirmation"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status        # Check current database status"
    echo "  $0 check         # Check what needs fixing"
    echo "  $0 fix           # Apply fixes with confirmation"
    echo "  $0 fix-force     # Apply fixes without confirmation"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    print_status "🔍 Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "app/main.py" ]; then
        print_error "❌ Error: Please run this script from the project root directory"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "❌ Error: Virtual environment not found"
        print_warning "💡 Please create a virtual environment first:"
        echo "   python -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        print_error "❌ Error: DATABASE_URL environment variable not set"
        print_warning "💡 Please set the DATABASE_URL environment variable"
        exit 1
    fi
    
    print_success "✅ Prerequisites check passed"
}

# Function to activate virtual environment
activate_venv() {
    print_status "🔧 Activating virtual environment..."
    source venv/bin/activate
    
    # Check if required packages are installed
    if ! python -c "import sqlalchemy" 2>/dev/null; then
        print_error "❌ Error: SQLAlchemy not installed"
        print_warning "💡 Please install requirements: pip install -r requirements.txt"
        exit 1
    fi
    
    print_success "✅ Virtual environment activated"
}

# Function to run status check
run_status() {
    print_status "📊 Checking database status..."
    python auto_fix_database.py --status
}

# Function to run check (dry run)
run_check() {
    print_status "🔍 Checking what needs to be fixed..."
    python auto_fix_database.py --check
}

# Function to run fix
run_fix() {
    local force=$1
    
    print_status "🔧 Applying database fixes..."
    
    if [ "$force" = "true" ]; then
        print_warning "⚠️  Force mode enabled - no confirmation required"
        python auto_fix_database.py --fix --verbose
    else
        print_warning "⚠️  This will modify your database schema!"
        echo ""
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python auto_fix_database.py --fix --verbose
        else
            print_warning "❌ Operation cancelled by user"
            exit 0
        fi
    fi
}

# Main script logic
main() {
    local command=$1
    
    case $command in
        "status")
            check_prerequisites
            activate_venv
            run_status
            ;;
        "check")
            check_prerequisites
            activate_venv
            run_check
            ;;
        "fix")
            check_prerequisites
            activate_venv
            run_fix false
            ;;
        "fix-force")
            check_prerequisites
            activate_venv
            run_fix true
            ;;
        "help"|"--help"|"-h"|"")
            show_usage
            ;;
        *)
            print_error "❌ Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
