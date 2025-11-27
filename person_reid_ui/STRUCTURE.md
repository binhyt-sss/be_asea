# Person ReID UI Module - Complete Structure

## ✅ Files Created

```
person_reid_ui/
├── 📄 README.md                 # Full documentation
├── 📄 QUICKSTART.md            # Quick start guide  
├── 📄 MIGRATION.md             # Migration guide
├── 📄 requirements.txt         # Python dependencies
├── 📄 config.yaml              # Configuration file
├── 📄 .env.example             # Environment template
├── 📄 .gitignore               # Git ignore
├── 📄 Dockerfile               # Docker build
├── 📄 docker-compose.yml       # Docker compose
├── 📄 start.ps1                # Windows start script
├── 📄 start.sh                 # Unix start script
├── 📄 app.py                   # Main Streamlit app
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── config.py              # Configuration loader
│   ├── api_client.py          # API HTTP client
│   └── utils.py               # Utility functions
│
└── pages/                      # Streamlit pages
    ├── 01_👥_Users.py         # User management (CREATED)
    ├── 02_🗺️_Zones.py        # Zone management (TEMPLATE BELOW)
    ├── 03_🚨_Alerts.py        # Real-time alerts (TEMPLATE BELOW)
    └── 04_📈_Statistics.py    # Statistics (TEMPLATE BELOW)
```

## 🎯 Key Features

### 1. Completely Standalone
- ✅ No backend code imports
- ✅ Only HTTP API calls
- ✅ Can run as separate repo
- ✅ Docker ready

### 2. Configuration Management
```python
# Three-tier priority:
1. Environment variables (highest)
2. config.yaml
3. Defaults (lowest)
```

### 3. API Client
```python
from src.api_client import get_api_client

api = get_api_client(
    base_url="http://localhost:8000",
    timeout=30,
    retry_attempts=3
)

# All endpoints available:
users = api.get_users()
zones = api.get_zones()
stats = api.get_user_stats()
```

### 4. Error Handling
```python
from src.api_client import APIError
from src.utils import show_error

try:
    user = api.create_user(...)
except APIError as e:
    show_error(f"Failed: {e}")
```

## 📝 Creating Additional Pages

### Template for Zones Page (02_🗺️_Zones.py)

```python
"""
Zone Management Page - Standalone Module
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from src.api_client import APIError
from src.utils import show_error, show_success, load_custom_css, create_zone_polygon_figure

st.set_page_config(page_title="Zones - Person ReID", page_icon="🗺️", layout="wide")
load_custom_css()

api = st.session_state.get('api_client')
config = st.session_state.get('config')

def main():
    st.title("🗺️ Zone Management")
    # ... implement zones CRUD similar to Users page
    # Use api.get_zones(), api.create_zone(), etc.

if __name__ == "__main__":
    main()
```

### Template for Alerts Page (03_🚨_Alerts.py)

```python
"""
Real-time Alerts Page - Standalone Module
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import time
from src.api_client import APIError
from src.utils import show_error, load_custom_css

st.set_page_config(page_title="Alerts - Person ReID", page_icon="🚨", layout="wide")
load_custom_css()

api = st.session_state.get('api_client')
config = st.session_state.get('config')

def main():
    st.title("🚨 Real-time Alerts")
    
    # Use api.get_recent_messages(limit=100)
    # Auto-refresh based on config.features.auto_refresh
    
    if config.features.auto_refresh:
        time.sleep(config.features.auto_refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
```

### Template for Statistics Page (04_📈_Statistics.py)

```python
"""
Statistics Page - Standalone Module
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import plotly.express as px
from src.api_client import APIError
from src.utils import show_error, load_custom_css, get_color_scheme

st.set_page_config(page_title="Statistics - Person ReID", page_icon="📈", layout="wide")
load_custom_css()

api = st.session_state.get('api_client')
config = st.session_state.get('config')

def main():
    st.title("📈 Statistics & Analytics")
    
    # Use api.get_user_stats(), api.get_zone_stats()
    # Create charts with plotly
    # Use config.charts.* for chart settings

if __name__ == "__main__":
    main()
```

## 🚀 Usage

### 1. Local Development
```powershell
cd person_reid_ui
.\start.ps1
```

### 2. Docker
```bash
docker-compose up -d
```

### 3. Production
```bash
export PERSON_REID_API_URL="https://api.production.com"
streamlit run app.py
```

## 🔧 Configuration Examples

### Minimal config.yaml
```yaml
api:
  base_url: "http://localhost:8000"
```

### Full config.yaml
```yaml
api:
  base_url: "http://localhost:8000"
  timeout: 30
  retry_attempts: 3

ui:
  title: "Person ReID System"
  layout: "wide"

features:
  auto_refresh: true
  auto_refresh_interval: 5
  debug_mode: false
```

### Environment Variables
```bash
# Most important
export PERSON_REID_API_URL="http://localhost:8000"

# Optional overrides
export PERSON_REID_DEBUG=true
export PERSON_REID_AUTO_REFRESH=false
```

## 📦 Dependencies

Only UI dependencies - no backend code needed:

```txt
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
requests>=2.31.0
pyyaml>=6.0.1
loguru>=0.7.0
```

## 🎯 Next Steps

1. ✅ Module structure created
2. ✅ Main app and config ready
3. ✅ API client implemented
4. ✅ Users page created
5. ⏳ Create Zones, Alerts, Statistics pages using templates above
6. ⏳ Test with backend API
7. ⏳ Deploy to production

## 💡 Tips

### 1. Copy old pages content
You can copy logic from old pages:
- `d:/be_asea/pages/02_🗺️_Zones.py` → Update imports
- `d:/be_asea/pages/03_🚨_Alerts.py` → Update imports
- `d:/be_asea/pages/04_📈_Statistics.py` → Update imports

### 2. Update imports pattern
```python
# Old (integrated)
from ui.api_helper import get_api_client

# New (standalone)
from src.api_client import get_api_client
api = st.session_state.api_client
```

### 3. Use config everywhere
```python
config = st.session_state.config

# Instead of hardcoding
limit = config.display.max_users_per_page  # Not: limit = 100
```

## ✅ Verification Checklist

- [ ] Can run `.\start.ps1` successfully
- [ ] UI loads without backend imports
- [ ] Config loads from config.yaml
- [ ] Environment variables override config
- [ ] API client connects to backend
- [ ] Error handling works gracefully
- [ ] Can build Docker image
- [ ] Docker compose works
- [ ] All pages accessible
- [ ] No import errors

## 🎉 Result

You now have a **completely independent UI module** that:
- Can run as a separate repository
- Has zero backend code dependencies
- Connects via HTTP API only
- Is Docker-ready
- Has flexible configuration
- Can scale independently

The old integrated UI still exists in the parent directory for backwards compatibility, but the new standalone module is the recommended approach!
