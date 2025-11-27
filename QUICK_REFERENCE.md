# Quick Reference - Async Backend

## 🎯 Core Principles

### 1. Everything is Async
```python
# ✅ DO: Use async/await everywhere
async def get_data():
    data = await db.execute(query)
    cached = await redis_cache.get("key")
    return data

# ❌ DON'T: Mix sync and async
async def get_data():
    data = sync_db_query()  # ❌ Blocks event loop!
    return data
```

### 2. Database Sessions (Dependency Injection)
```python
from database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # Session auto-managed: commit, rollback, close
    users = await user_crud.get_all_users(db)
    return users
```

### 3. Redis Cache Operations
```python
from utils.redis_cache import RedisCache

# All Redis methods are async
redis_cache = RedisCache(redis_config=settings.redis)

# Cache data
await redis_cache.cache_users_dict(data, ttl=3600)

# Get cached data
cached = await redis_cache.get_users_dict()

# Invalidate cache
await redis_cache.invalidate_users_dict()

# Get stats
stats = await redis_cache.get_stats()

# Cleanup on shutdown
await redis_cache.close()
```

### 4. CRUD Operations
```python
from crud import user_crud, zone_crud

# All CRUD operations are async
async def example(db: AsyncSession):
    # Get all
    users = await user_crud.get_all_users(db, skip=0, limit=100)
    
    # Get by ID
    user = await user_crud.get_user_by_id(db, user_id=1)
    
    # Create
    new_user = await user_crud.create_user(db, user_data)
    
    # Update
    updated_user = await user_crud.update_user(db, user_id, update_data)
    
    # Delete
    success = await user_crud.delete_user(db, user_id)
    
    # Statistics
    count = await user_crud.count_users(db)
    users_dict = await user_crud.get_users_dict(db)
```

---

## 📝 Common Patterns

### Pattern 1: Cache-Aside with Invalidation
```python
@app.get("/users-dict")
async def get_users_dict(
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db)
):
    # Try cache first
    if use_cache and redis_cache.is_available():
        cached_dict = await redis_cache.get_users_dict()
        if cached_dict:
            return cached_dict
    
    # Fallback to database
    users_dict = await user_crud.get_users_dict(db)
    
    # Update cache
    if redis_cache.is_available():
        await redis_cache.cache_users_dict(users_dict, ttl=3600)
    
    return users_dict

@app.post("/users")
async def create_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await user_crud.create_user(db, user_data)
    
    # Invalidate cache on write
    await redis_cache.invalidate_users_dict()
    
    return user
```

### Pattern 2: Eager Loading with Relationships
```python
from sqlalchemy.orm import selectinload

async def get_zone_with_users(db: AsyncSession, zone_id: str):
    stmt = (
        select(WorkingZone)
        .options(selectinload(WorkingZone.users))  # Eager load
        .where(WorkingZone.zone_id == zone_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### Pattern 3: Transactions
```python
async def transfer_user_to_zone(
    db: AsyncSession,
    user_id: int,
    new_zone_id: str
):
    try:
        # Get user
        user = await user_crud.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update zone
        user.zone_id = new_zone_id
        await db.commit()  # Explicit commit
        
        # Invalidate cache
        await redis_cache.invalidate_users_dict()
        
        return user
    except Exception as e:
        await db.rollback()  # Rollback on error
        raise
```

### Pattern 4: Batch Operations
```python
async def bulk_create_users(
    db: AsyncSession,
    users_data: List[schemas.UserCreate]
):
    users = []
    for user_data in users_data:
        user = User(
            global_id=user_data.global_id,
            name=user_data.name,
            zone_id=user_data.zone_id
        )
        users.append(user)
        db.add(user)
    
    await db.commit()
    
    # Refresh to get IDs
    for user in users:
        await db.refresh(user)
    
    # Invalidate cache once
    await redis_cache.invalidate_users_dict()
    
    return users
```

---

## 🧪 Testing

### Unit Test Example
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def db_session():
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(db_session):
    user_data = schemas.UserCreate(
        global_id=1001,
        name="Test User",
        zone_id="ZONE_001"
    )
    
    user = await user_crud.create_user(db_session, user_data)
    
    assert user.id is not None
    assert user.global_id == 1001
    assert user.name == "Test User"
```

### Integration Test Example
```python
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

---

## 🚨 Common Mistakes

### ❌ Mistake 1: Forgetting `await`
```python
# ❌ Wrong: Returns coroutine, doesn't execute
users = user_crud.get_all_users(db)

# ✅ Correct: Actually executes and waits
users = await user_crud.get_all_users(db)
```

### ❌ Mistake 2: Blocking I/O in async function
```python
# ❌ Wrong: time.sleep blocks event loop
async def slow_endpoint():
    time.sleep(5)  # ❌ Blocks entire app!
    return "Done"

# ✅ Correct: asyncio.sleep is non-blocking
async def slow_endpoint():
    await asyncio.sleep(5)  # ✅ Other requests continue
    return "Done"
```

### ❌ Mistake 3: Not closing connections
```python
# ❌ Wrong: Connection leak
@app.on_event("shutdown")
async def shutdown():
    pass  # Connections left open!

# ✅ Correct: Clean shutdown
@app.on_event("shutdown")
async def shutdown():
    await redis_cache.close()
    await close_db()
```

### ❌ Mistake 4: Mixing sync and async Redis
```python
# ❌ Wrong: Using sync Redis methods
async def endpoint():
    redis_cache.redis.get("key")  # ❌ Blocks!

# ✅ Correct: Using async methods
async def endpoint():
    await redis_cache.get("key")  # ✅ Non-blocking
```

---

## 📊 Performance Tips

### 1. Use Connection Pooling
```python
# Already configured in database/session.py
create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Max connections
    max_overflow=10,     # Extra connections under load
    pool_recycle=3600,   # Recycle after 1 hour
    pool_pre_ping=True   # Check connections
)
```

### 2. Batch Database Queries
```python
# ✅ Good: Single query
users = await db.execute(
    select(User).where(User.zone_id.in_(zone_ids))
)

# ❌ Bad: N+1 queries
for zone_id in zone_ids:
    users = await db.execute(
        select(User).where(User.zone_id == zone_id)
    )
```

### 3. Cache Hot Data
```python
# Cache frequently accessed data
users_dict = await redis_cache.get_users_dict()
if not users_dict:
    users_dict = await user_crud.get_users_dict(db)
    await redis_cache.cache_users_dict(users_dict, ttl=3600)
```

### 4. Use Lazy Loading for Relationships
```python
# Only load when needed
zone = await zone_crud.get_zone_by_id(db, zone_id)
# Users not loaded yet

# Load on demand
if need_users:
    zone_with_users = await zone_crud.get_zone_with_users(db, zone_id)
```

---

## 🔗 Quick Links

- **Main API**: `main.py`
- **Database Models**: `database/models.py`
- **Schemas**: `schemas/database.py`
- **CRUD**: `crud/user_crud.py`, `crud/zone_crud.py`
- **Redis Cache**: `utils/redis_cache.py`
- **Configuration**: `config/settings.py`
- **Migrations**: `alembic/versions/`

---

## 📚 Documentation

- [Full README](README.md)
- [Async Improvements](ASYNC_IMPROVEMENTS.md)
- [API Documentation](http://localhost:8000/docs)

---

**Keep it Async, Keep it Fast! ⚡**
