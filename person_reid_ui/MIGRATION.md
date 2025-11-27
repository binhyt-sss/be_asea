# Migration Guide - Moving from Integrated to Standalone UI

This guide helps you migrate from the integrated UI to the standalone UI module.

## Overview

The UI has been refactored into a standalone module with:
- ✅ No backend code dependencies
- ✅ Independent configuration
- ✅ Can run as separate repository
- ✅ Docker support
- ✅ Environment-based configuration

## Quick Migration

### Option 1: Use as Submodule in Current Repo

The UI is already in `person_reid_ui/` directory and ready to use:

```powershell
cd person_reid_ui
.\start.ps1
```

### Option 2: Extract to Separate Repository

```bash
# 1. Copy the person_reid_ui folder to new location
cp -r person_reid_ui /path/to/new/repo

# 2. Initialize git (optional)
cd /path/to/new/repo
git init
git add .
git commit -m "Initial commit - Person ReID UI Module"

# 3. Run standalone
.\start.ps1
```

## Configuration Changes

### Old Way (Integrated)
```python
# Had to import from backend
from config import get_settings
from database.session import get_db

settings = get_settings()
```

### New Way (Standalone)
```python
# Independent configuration
from src.config import get_config
from src.api_client import get_api_client

config = get_config()  # Loads from config.yaml or env vars
api = get_api_client(config.api.base_url)
```

## API Connection

### Old Way
```python
# UI and backend in same process
# Direct database access
```

### New Way
```python
# UI connects to backend via HTTP API
# Configured through config.yaml or environment variables

# config.yaml
api:
  base_url: "http://localhost:8000"
  
# Or environment variable
export PERSON_REID_API_URL="http://your-api:8000"
```

## Running the Standalone UI

### Local Development

```powershell
# Windows
cd person_reid_ui
.\start.ps1

# Linux/Mac
cd person_reid_ui
./start.sh
```

### Docker

```bash
cd person_reid_ui

# Build and run
docker-compose up -d

# Or build manually
docker build -t person-reid-ui .
docker run -p 8501:8501 -e PERSON_REID_API_URL=http://api:8000 person-reid-ui
```

### Production

```bash
# 1. Set environment variables
export PERSON_REID_API_URL="https://api.production.com"
export PERSON_REID_UI_PORT=8501

# 2. Run with production settings
streamlit run app.py --server.port $PERSON_REID_UI_PORT
```

## File Structure Comparison

### Old Structure
```
be_asea/
├── main.py (backend)
├── config/ (shared)
├── database/ (backend)
├── streamlit_app.py (UI)
├── pages/ (UI)
└── ui/ (UI helper - imports backend)
```

### New Structure
```
person_reid_ui/ (standalone)
├── app.py (main UI)
├── config.yaml (UI config)
├── requirements.txt (UI deps only)
├── src/
│   ├── config.py (independent)
│   ├── api_client.py (HTTP only)
│   └── utils.py (UI helpers)
└── pages/
    ├── 01_👥_Users.py
    ├── 02_🗺️_Zones.py
    ├── 03_🚨_Alerts.py
    └── 04_📈_Statistics.py
```

## Benefits of Standalone Module

1. **Independent Deployment**
   - UI can scale separately from backend
   - Deploy to different servers/containers
   - Different release cycles

2. **No Code Coupling**
   - UI doesn't import backend code
   - Changes in backend don't break UI
   - Clear API contract

3. **Easier Development**
   - UI developers don't need backend setup
   - Can mock API for testing
   - Faster iteration

4. **Flexible Deployment**
   - Docker container
   - Kubernetes pod
   - Static hosting with API proxy
   - Separate repository

## Configuration Priority

The standalone UI loads configuration in this order (highest to lowest priority):

1. **Environment Variables**
   ```bash
   PERSON_REID_API_URL=http://api:8000
   ```

2. **config.yaml**
   ```yaml
   api:
     base_url: "http://localhost:8000"
   ```

3. **Defaults**
   ```python
   # Hard-coded defaults in src/config.py
   base_url = "http://localhost:8000"
   ```

## Troubleshooting

### UI can't connect to API

```bash
# Check API is running
curl http://localhost:8000/health

# Update configuration
export PERSON_REID_API_URL="http://correct-url:8000"

# Or edit config.yaml
api:
  base_url: "http://correct-url:8000"
```

### Import errors

Make sure you're using the standalone module imports:

```python
# ❌ Old (won't work)
from config import get_settings
from ui.api_helper import get_api_client

# ✅ New (standalone)
from src.config import get_config
from src.api_client import get_api_client
```

### Dependencies missing

```bash
# Install UI dependencies
pip install -r requirements.txt

# Note: No backend dependencies needed!
```

## Backwards Compatibility

The old integrated UI files are still in the parent directory for backwards compatibility:
- `streamlit_app.py`
- `pages/`
- `ui/`

You can continue using them, but they're not recommended for new deployments.

## Next Steps

1. ✅ Run standalone UI locally
2. ✅ Configure API connection
3. ✅ Test all features work
4. ✅ Deploy to production
5. ✅ (Optional) Move to separate repository

## Support

For issues or questions:
- Check README.md
- Review config.yaml settings
- Check API connection
- Enable debug mode: `PERSON_REID_DEBUG=true`
