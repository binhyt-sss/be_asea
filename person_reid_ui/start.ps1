# Quick start script for Person ReID UI
# Standalone module

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Person ReID UI - Standalone Module   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "app.py")) {
    Write-Host "❌ Error: app.py not found!" -ForegroundColor Red
    Write-Host "   Please run this script from the person_reid_ui directory" -ForegroundColor Yellow
    exit 1
}

# Check Python
Write-Host "🐍 Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Load configuration
if (Test-Path ".env") {
    Write-Host "⚙️  Loading configuration from .env" -ForegroundColor Cyan
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "⚠️  No .env file found, using defaults" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env to customize" -ForegroundColor Yellow
}

# Get API URL from config or env
$apiUrl = $env:PERSON_REID_API_URL
if (-not $apiUrl) {
    $apiUrl = "http://localhost:8000"
}

Write-Host ""
Write-Host "🔍 Configuration:" -ForegroundColor Cyan
Write-Host "   API URL: $apiUrl" -ForegroundColor White
Write-Host "   UI Port: 8501" -ForegroundColor White
Write-Host ""

# Check API availability
Write-Host "🔌 Checking API connection..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "✅ API is available at $apiUrl" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Cannot reach API at $apiUrl" -ForegroundColor Yellow
    Write-Host "   The UI will still start, but features may not work" -ForegroundColor Yellow
    Write-Host "   Make sure the backend is running!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starting Streamlit UI..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 UI will be available at:" -ForegroundColor Green
Write-Host "   http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "💡 Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Streamlit
streamlit run app.py --server.port 8501 --server.address localhost
