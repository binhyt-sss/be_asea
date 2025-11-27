# Person ReID UI Module

Standalone Streamlit UI for Person Re-Identification System.

## 📦 Standalone Module

This UI module can run independently as a separate repository. It only requires the backend API URL to function.

## 🚀 Quick Start

### Option 1: Run from this directory

```powershell
cd person_reid_ui
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Option 2: Clone as separate repo

```bash
git clone <this-ui-repo>
cd person_reid_ui
pip install -r requirements.txt
streamlit run app.py
```

## ⚙️ Configuration

Edit `config.yaml` or set environment variables:

```yaml
api:
  base_url: "http://localhost:8000"
  timeout: 30

ui:
  title: "Person ReID System"
  port: 8501
  theme: "light"
```

Or use environment variables:
```bash
export PERSON_REID_API_URL="http://your-api-server:8000"
export PERSON_REID_UI_PORT=8501
```

## 📁 Module Structure

```
person_reid_ui/
├── app.py                    # Main Streamlit application
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── src/
│   ├── __init__.py
│   ├── config.py            # Config loader
│   ├── api_client.py        # API client
│   └── utils.py             # Utility functions
├── pages/
│   ├── 01_👥_Users.py       # User management
│   ├── 02_🗺️_Zones.py      # Zone management
│   ├── 03_🚨_Alerts.py      # Real-time alerts
│   └── 04_📈_Statistics.py  # Statistics
└── assets/
    └── styles.css            # Custom CSS
```

## 🔌 API Requirements

The backend API must provide these endpoints:

- `GET /health` - Health check
- `GET /users` - List users
- `POST /users` - Create user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user
- `GET /zones` - List zones
- `POST /zones` - Create zone
- `PUT /zones/{id}` - Update zone
- `DELETE /zones/{id}` - Delete zone
- `GET /stats/users` - User statistics
- `GET /stats/zones` - Zone statistics
- `GET /messages/recent` - Recent Kafka messages

## 🎨 Features

- **Standalone**: No dependency on backend code
- **Configurable**: YAML config + environment variables
- **Portable**: Can be deployed separately
- **Type-safe**: Full type hints
- **Error handling**: Graceful degradation
- **Cached**: Optimized with Streamlit caching

## 🐳 Docker Support

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t person-reid-ui .
docker run -p 8501:8501 -e PERSON_REID_API_URL=http://api:8000 person-reid-ui
```

## 📝 Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
black src/ pages/

# Type check
mypy src/

# Run tests
pytest tests/
```

## 🌐 Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set `PERSON_REID_API_URL` in secrets

### Docker Compose
```yaml
version: '3.8'
services:
  ui:
    build: .
    ports:
      - "8501:8501"
    environment:
      PERSON_REID_API_URL: http://backend:8000
```

### Kubernetes
See `k8s/` directory for manifests.

## 📊 Tech Stack

- **Streamlit**: UI framework
- **Plotly**: Interactive charts
- **Requests**: HTTP client
- **PyYAML**: Config parsing
- **Pandas**: Data manipulation

## 🤝 Contributing

This is a standalone module. Contributions welcome!

## 📄 License

MIT License
