"""
API Endpoints Documentation
Complete list of all available endpoints
"""

## User Management Endpoints

### GET /users
Get all users with pagination
- Query params: `skip` (default: 0), `limit` (default: 100)
- Returns: List[User]

### GET /users/{user_id}
Get user by ID
- Path param: `user_id` (int)
- Returns: User
- Error: 404 if not found

### POST /users
Create new user
- Body: UserCreate schema
- Returns: User
- Error: 400 if global_id already exists
- Side effect: Invalidates Redis users cache

### PUT /users/{user_id}
Update existing user
- Path param: `user_id` (int)
- Body: UserUpdate schema
- Returns: User
- Error: 404 if not found
- Side effect: Invalidates Redis users cache

### DELETE /users/{user_id}
Delete user
- Path param: `user_id` (int)
- Returns: Success message
- Error: 404 if not found
- Side effect: Invalidates Redis users cache

### GET /users-dict
Get users dictionary (cached)
- Query param: `use_cache` (default: true)
- Returns: Dict[global_id, user_name]
- Caching: TTL 3600 seconds

### GET /users/by-zone/{zone_id}
Get all users in a specific zone
- Path param: `zone_id` (str)
- Returns: List[User]

---

## Zone Management Endpoints

### GET /zones
Get all zones with pagination
- Query params: `skip` (default: 0), `limit` (default: 100)
- Returns: List[WorkingZone]

### GET /zones/{zone_id}
Get zone by ID
- Path param: `zone_id` (str)
- Returns: WorkingZone
- Error: 404 if not found

### POST /zones
Create new zone
- Body: WorkingZoneCreate schema
- Returns: WorkingZone
- Error: 400 if zone_id already exists

### PUT /zones/{zone_id}
Update existing zone
- Path param: `zone_id` (str)
- Body: WorkingZoneUpdate schema
- Returns: WorkingZone
- Error: 404 if not found

### DELETE /zones/{zone_id}
Delete zone
- Path param: `zone_id` (str)
- Returns: Success message
- Error: 404 if not found
- Warning: Cascade deletes all users in zone

---

## Statistics Endpoints

### GET /stats/users
Get user statistics
- Returns: `{"total_users": int}`

### GET /stats/zones
Get zone statistics with user counts
- Returns: `{"total_zones": int, "zones": [...]}`

---

## Kafka Streaming Endpoints

### WS /ws/alerts
WebSocket for real-time Kafka alerts
- Protocol: WebSocket
- Sends: JSON messages from Kafka stream

### GET /messages/recent
Get recent Kafka messages
- Query param: `limit` (default: 50)
- Returns: `{"count": int, "messages": [...]}`

---

## Cache Management Endpoints

### GET /cache/stats
Get Redis cache statistics
- Returns: Cache metrics (hits, misses, keys, memory)

### POST /cache/invalidate/users-dict
Invalidate users dictionary cache
- Returns: Success message

---

## Health & Status Endpoints

### GET /
Root endpoint with API information
- Returns: Service metadata and endpoints list

### GET /health
Health check with service status
- Returns: System status including DB, Redis, Kafka status
