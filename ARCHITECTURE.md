# Async Architecture Diagram

## Request Flow (Fully Non-Blocking)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Request                          │
│                    GET /users?limit=100                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Event Loop                           │
│                  (Single Thread, Many Tasks)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dependency Injection                         │
│              db: AsyncSession = Depends(get_db)                 │
│                                                                 │
│  async def get_db():                                            │
│      async with AsyncSessionLocal() as session:                │
│          yield session  # ✅ Auto-managed lifecycle             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Endpoint Handler                          │
│    @app.get("/users")                                           │
│    async def get_users(db: AsyncSession = Depends(get_db)):    │
│        return await user_crud.get_all_users(db, limit=100)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CRUD Operation                            │
│    async def get_all_users(db: AsyncSession, limit: int):      │
│        stmt = select(User).limit(limit)                         │
│        result = await db.execute(stmt)  # ⚡ Async I/O         │
│        return result.scalars().all()                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLAlchemy Async Engine                      │
│                   (Connection Pooling)                          │
│                                                                 │
│  pool_size=20, max_overflow=10                                  │
│  ⚡ Non-blocking connection checkout                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       asyncpg Driver                            │
│              ⚡ Non-blocking PostgreSQL I/O                    │
│                                                                 │
│  - Async query execution                                        │
│  - Async result fetching                                        │
│  - Zero thread blocking                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                          │
│                   localhost:5432/hailt_imespro                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ (Query executes)
                             │
                             ▼ (Results ready)
┌─────────────────────────────────────────────────────────────────┐
│                    Response to Client                           │
│            [{id: 1, name: "User A"}, ...]                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Redis Cache Flow (Async)

```
┌─────────────────────────────────────────────────────────────────┐
│                Client Request: GET /users-dict                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Endpoint Handler                             │
│    @app.get("/users-dict")                                      │
│    async def get_users_dict(db: AsyncSession):                  │
│        # Try cache first                                        │
│        cached = await redis_cache.get_users_dict() # ⚡ Async   │
│        if cached:                                               │
│            return cached  # 🚀 Fast path                        │
│        # Cache miss - query DB                                  │
│        data = await user_crud.get_users_dict(db)  # ⚡ Async    │
│        await redis_cache.cache_users_dict(data)   # ⚡ Async    │
│        return data                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │   Redis Cache       │   │   PostgreSQL DB     │
    │   (redis.asyncio)   │   │   (asyncpg)         │
    │                     │   │                     │
    │  ⚡ Non-blocking    │   │  ⚡ Non-blocking    │
    │  - hgetall()        │   │  - SELECT ...       │
    │  - hset()           │   │  - FROM user        │
    │  - expire()         │   │  - JOIN zone        │
    └─────────────────────┘   └─────────────────────┘
```

---

## Concurrent Request Handling

### Single Request (Before: Sync Redis)
```
Request 1:
├─ Database Query (50ms) ⚡ Async
└─ Redis Get (5ms)       ❌ BLOCKS

Total: 55ms (one request at a time)
```

### 100 Concurrent Requests (Before: Sync Redis)
```
Request 1:  [DB ⚡][Redis ❌]
Request 2:         [DB ⚡][Redis ❌]
Request 3:                [DB ⚡][Redis ❌]
...
Request 100:                            [DB ⚡][Redis ❌]

Total: 50ms (DB concurrent) + 500ms (Redis serialized) = 550ms
```

### 100 Concurrent Requests (After: Async Redis)
```
Request 1:  [DB ⚡][Redis ⚡]
Request 2:  [DB ⚡][Redis ⚡]
Request 3:  [DB ⚡][Redis ⚡]
...
Request 100:[DB ⚡][Redis ⚡]

Total: 50ms (DB concurrent) + 5ms (Redis concurrent) = 55ms ✅ 10x faster!
```

---

## Component Interaction

```
┌───────────────────────────────────────────────────────────────┐
│                        main.py                                │
│                   (FastAPI Application)                       │
│                                                               │
│  • Startup: Init DB, Redis, Kafka                             │
│  • Endpoints: All async                                       │
│  • Shutdown: Graceful cleanup                                 │
└───────────────┬───────────────────────────────────────────────┘
                │
        ┌───────┼───────┐
        │       │       │
        ▼       ▼       ▼
    ┌─────┐ ┌─────┐ ┌─────┐
    │ DB  │ │Redis│ │Kafka│
    │     │ │     │ │     │
    │async│ │async│ │ 🧵  │
    └──┬──┘ └──┬──┘ └──┬──┘
       │       │       │
       ▼       ▼       │
    ┌─────┐ ┌─────┐   │
    │crud/│ │utils│   │
    │     │ │redis│   │
    │async│ │_cache│  │
    └──┬──┘ └──┬──┘   │
       │       │       │
       ▼       ▼       ▼
    ┌─────┐ ┌─────┐ ┌─────┐
    │models│ │config│ │buffer│
    └─────┘ └─────┘ └─────┘
```

---

## Lifecycle Events

### Startup Sequence
```
1. FastAPI app.on_event("startup")
   │
2. ├─ await init_db()
   │   └─ Create async engine
   │       └─ Test connection pool
   │
3. ├─ RedisCache initialization
   │   └─ Lazy connection (on first use)
   │       └─ await redis.ping()
   │
4. └─ Start Kafka consumer (background thread)
       └─ Non-blocking message handler
```

### Shutdown Sequence
```
1. FastAPI app.on_event("shutdown")
   │
2. ├─ await redis_cache.close()
   │   └─ await redis.close()
   │
3. ├─ await close_db()
   │   └─ await engine.dispose()
   │
4. └─ kafka_consumer.close()
       └─ Thread join(timeout=5)
```

### Request Lifecycle
```
1. Request arrives
   │
2. FastAPI creates task
   │
3. Dependency injection: get_db()
   │   └─ Checkout session from pool
   │
4. Execute endpoint handler
   │   ├─ await db.execute(...)  # Async
   │   └─ await redis_cache.get(...) # Async
   │
5. Response sent
   │
6. Session auto-closed (context manager)
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Endpoint Handler                         │
│    async def create_user(db, user_data):                    │
│        try:                                                 │
│            user = await user_crud.create_user(db, user_data)│
│            await redis_cache.invalidate_users_dict()        │
│            return user                                      │
│        except Exception as e:                               │
│            await db.rollback()  # Auto-rollback             │
│            raise HTTPException(...)                         │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
           SUCCESS                     ERROR
                │                         │
                ▼                         ▼
        ┌─────────────┐         ┌──────────────┐
        │ db.commit() │         │ db.rollback()│
        │   (auto)    │         │   (auto)     │
        └─────────────┘         └──────────────┘
                │                         │
                ▼                         ▼
        ┌─────────────┐         ┌──────────────┐
        │Cache cleared│         │ HTTP 500     │
        └─────────────┘         └──────────────┘
```

---

## Performance Monitoring

### Metrics to Track

```python
# Database connection pool
from database.session import engine

pool_stats = {
    "pool_size": engine.pool.size(),
    "checked_out": engine.pool.checkedout(),
    "overflow": engine.pool.overflow(),
    "waiters": engine.pool._overflow
}

# Redis cache stats
redis_stats = await redis_cache.get_stats()
# Returns: total_keys, memory_used, connected_clients

# Request timing
import time
start = time.perf_counter()
result = await endpoint_handler()
duration = time.perf_counter() - start
```

### Alerting Thresholds

```
⚠️  Warning:
- DB pool > 15 connections checked out
- Redis memory > 100MB
- Response time > 500ms

❌ Critical:
- DB pool exhausted (20+ connections)
- Redis connection errors
- Response time > 1000ms
```

---

## Best Practices Checklist

✅ **Async Everywhere**
- [x] All database operations use `await`
- [x] All Redis operations use `await`
- [x] No blocking I/O in async functions

✅ **Resource Management**
- [x] Sessions auto-managed by Depends()
- [x] Connections closed on shutdown
- [x] Connection pooling configured

✅ **Error Handling**
- [x] Try/except in critical paths
- [x] Auto-rollback on errors
- [x] Graceful degradation (Redis optional)

✅ **Performance**
- [x] Lazy connection initialization
- [x] Eager loading for relationships
- [x] Cache hot data with TTL

✅ **Testing**
- [x] Unit tests for CRUD
- [x] Integration tests for endpoints
- [x] Stress tests for concurrency

---

**Built with async/await, optimized for performance! ⚡**
