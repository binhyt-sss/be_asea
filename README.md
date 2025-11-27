# Person ReID Backend - Async SQLAlchemy Edition

Modern async backend for Person Re-Identification system with PostgreSQL, Redis, Kafka, and Qdrant.

## 🚀 Features

- ⚡ **Async SQLAlchemy 2.0** - Non-blocking database operations with asyncpg
- 🎯 **Dependency Injection** - Clean architecture with FastAPI Depends
- 📊 **Unified API** - Database + Kafka WebSocket on single port (8000)
- 🔄 **Connection Pooling** - Efficient resource management (pool_size=20)
- 🗄️ **Alembic Migrations** - Version-controlled database schema
- 📦 **Redis Caching** - Fast dictionary lookups with auto-invalidation
- 📨 **Kafka Streaming** - Real-time alerts via WebSocket
- 🎨 **Streamlit UI** - Interactive testing interface
- 🧪 **Stress Testing** - Concurrent request benchmarks

## 📋 Requirements

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+
- Kafka (Confluent KRaft)

## 🛠️ Quick Setup

### 1. Clone & Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install all dependencies
pip install -r requirements.txt
# Or use uv for faster installation
uv pip install -r requirements.txt
```

### 2. Start Docker Services

```bash
# Start PostgreSQL, Redis, Kafka, Qdrant
docker-compose -f deployment/docker-compose.yml up -d

# Add kafka-broker to hosts file (Windows - run as Administrator)
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 kafka-broker"

# Check services are running
docker-compose -f deployment/docker-compose.yml ps
```

### 3. Setup Environment Variables

The `.env` file is already configured with defaults:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=hailt
POSTGRES_PASSWORD=1
POSTGRES_DATABASE=hailt_imespro

# Redis
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=kafka-broker:9092
KAFKA_TOPIC=person_reid_alerts
```

### 4. Run Database Migrations

```bash
# Create tables using Alembic
alembic upgrade head

# Or let the app create them automatically on startup
```

### 5. Seed Sample Data (Optional)

```bash
python seed_data.py
```

### 6. Start the Backend

```bash
# Option 1: Run unified API (recommended)
python main.py

# Option 2: Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Open Testing UI

```bash
# In a new terminal
streamlit run ui/test_app.py --server.port 8501
```

## 🌐 Endpoints

### Unified API: http://localhost:8000

#### Database Operations
- `GET /users` - List all users
- `POST /users` - Create user
- `GET /users/{id}` - Get user by ID
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user
- `GET /users-dict` - Get users dictionary (cached)

#### Zone Management
- `GET /zones` - List all zones
- `POST /zones` - Create zone
- `GET /zones/{id}` - Get zone by ID

#### Statistics
- `GET /stats/users` - User count
- `GET /stats/zones` - Zone stats with user counts

#### Kafka Streaming
- `WS /ws/alerts` - WebSocket for real-time alerts
- `GET /messages/recent` - Get recent Kafka messages

#### Cache Management
- `GET /cache/stats` - Redis statistics
- `POST /cache/invalidate/users-dict` - Clear users cache

#### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
- `GET /health` - Health check

### Testing UI: http://localhost:8501

Interactive Streamlit interface with:
- 📊 Dashboard with metrics
- 👥 User CRUD operations
- 🏢 Zone management with polygon visualization
- 📈 Statistics and charts
- ⚙️ Cache management

## 🧪 Testing

### Run Stress Tests

```bash
python stress_test.py
```

Tests concurrent performance:
- 100 concurrent reads
- 50 concurrent writes
- Mixed read/write workload

Expected results: >100 requests/second

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get all users
curl http://localhost:8000/users

# Create user
curl -X POST http://localhost:8000/users `
  -H "Content-Type: application/json" `
  -d '{\"global_id\": 1001, \"name\": \"Test User\", \"zone_id\": \"ZONE_001\"}'
```

## 📁 Project Structure

```
be_asea/
├── main.py                    # Unified API entry point
├── api/
│   ├── database_service.py    # Database API (deprecated - merged to main.py)
│   └── kafka_consumer_service.py  # Kafka API (deprecated - merged to main.py)
├── crud/
│   ├── user_crud.py           # User CRUD operations
│   └── zone_crud.py           # Zone CRUD operations
├── database/
│   ├── models.py              # SQLAlchemy ORM models
│   ├── session.py             # Async session management
│   └── postgres_manager.py    # Old sync manager (deprecated)
├── schemas/
│   └── database.py            # Pydantic DTOs
├── utils/
│   ├── kafka_manager.py       # Kafka producer/consumer
│   └── redis_cache.py         # Redis caching
├── config/
│   └── settings.py            # Centralized configuration
├── ui/
│   └── test_app.py            # Streamlit testing UI
├── alembic/
│   └── versions/              # Database migrations
├── deployment/
│   └── docker-compose.yml     # All services
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

All settings in `config/settings.py` with environment variable support:

- **Database**: Async PostgreSQL with connection pooling
- **Redis**: Optional caching with auto-invalidation
- **Kafka**: Optional streaming with WebSocket relay
- **Logging**: Loguru with configurable levels

## 🚀 Performance

### Async Benefits (vs Blocking)

- **Concurrency**: Handles 100+ requests simultaneously
- **Response Time**: Mean ~300-400ms under load
- **Throughput**: 100-200 requests/second
- **Resource Usage**: Efficient connection pooling

### Benchmarks (from stress_test.py)

```
✅ 100 concurrent reads:  101.56 req/s (0.985s total)
✅ 50 concurrent writes:  107.76 req/s (0.464s total)
✅ Mixed workload:        188.43 req/s (0.531s total)
```

## 📚 Database Schema

### User Table
```sql
- id: INTEGER PRIMARY KEY
- global_id: INTEGER UNIQUE
- name: VARCHAR
- zone_id: VARCHAR (FK to working_zone)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### WorkingZone Table
```sql
- zone_id: VARCHAR PRIMARY KEY
- zone_name: VARCHAR
- x1, y1, x2, y2, x3, y3, x4, y4: FLOAT (polygon coordinates)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

## 🔄 Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🐛 Troubleshooting

### Kafka hostname issues
```bash
# Windows (as Administrator)
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 kafka-broker"

# Linux/Mac
echo "127.0.0.1 kafka-broker" | sudo tee -a /etc/hosts
```

### Database connection errors
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U hailt -d hailt_imespro
```

### Port already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <pid> /F
```

## 📝 Development

### Add new endpoint

1. Create CRUD function in `crud/`
2. Add route in `main.py`
3. Update Pydantic schemas in `schemas/`
4. Create migration: `alembic revision --autogenerate`

### Run in development mode

```bash
uvicorn main:app --reload --log-level debug
```

## 📄 License

MIT License - See LICENSE file

## 👥 Contributors

- Backend Architecture: Async SQLAlchemy + FastAPI
- Database: PostgreSQL with asyncpg driver
- Caching: Redis
- Messaging: Apache Kafka
- Vector DB: Qdrant

---

**Built with ❤️ using FastAPI, SQLAlchemy 2.0, and asyncpg**
