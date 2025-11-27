#!/bin/bash
# Quick start script for Person ReID UI (Unix/Linux/Mac)

echo "========================================"
echo "  Person ReID UI - Standalone Module  "
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found!"
    echo "   Please run this script from the person_reid_ui directory"
    exit 1
fi

# Check Python
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✅ $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Load configuration
if [ -f ".env" ]; then
    echo "⚙️  Loading configuration from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using defaults"
    echo "   Copy .env.example to .env to customize"
fi

# Get API URL from config or env
API_URL=${PERSON_REID_API_URL:-http://localhost:8000}

echo ""
echo "🔍 Configuration:"
echo "   API URL: $API_URL"
echo "   UI Port: 8501"
echo ""

# Check API availability
echo "🔌 Checking API connection..."
if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    echo "✅ API is available at $API_URL"
else
    echo "⚠️  Cannot reach API at $API_URL"
    echo "   The UI will still start, but features may not work"
    echo "   Make sure the backend is running!"
fi

echo ""
echo "🚀 Starting Streamlit UI..."
echo ""
echo "📱 UI will be available at:"
echo "   http://localhost:8501"
echo ""
echo "💡 Press Ctrl+C to stop"
echo ""
echo "========================================"
echo ""

# Start Streamlit
streamlit run app.py --server.port 8501 --server.address localhost
