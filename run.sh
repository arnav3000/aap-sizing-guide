#!/bin/bash
# Startup script for AAP Sizing Calculator

echo "==================================================="
echo "  AAP 2.4 to 2.6 Sizing Calculator"
echo "==================================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment and check dependencies
echo "Checking dependencies..."
source venv/bin/activate

python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

echo "Starting web server..."
echo ""
echo "✅ Server is running!"
echo ""
echo "📍 Open your browser and navigate to:"
echo "   http://localhost:5001"
echo ""
echo "💡 Tips:"
echo "   - Click 'Load Example Data' to see your scenario"
echo "   - Click 'Calculate Sizing' to get recommendations"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 app.py
