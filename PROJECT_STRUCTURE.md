# License SKU Microservice - Project Structure

## Directory Layout

```
licence-sku-microservice/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # SQLAlchemy setup
│   ├── redis_client.py         # Redis client and cache utilities
│   │
│   ├── models/                 # Database models
│   │   └── __init__.py         # SQLAlchemy ORM models
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   └── __init__.py         # All API schemas
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── sku_service.py      # SKU management logic
│   │   ├── license_service.py  # License lifecycle logic
│   │   └── validation_engine.py # License validation logic
│   │
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   ├── products.py         # Product management endpoints
│   │   ├── skus.py             # SKU management endpoints
│   │   ├── licenses.py         # License management endpoints
│   │   ├── validation.py       # License validation endpoints
│   │   └── api_keys.py         # API key management endpoints
│   │
│   ├── middleware/             # HTTP middleware
│   │   ├── __init__.py
│   │   └── auth.py             # Authentication, rate limiting, CORS
│   │
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── auth.py             # JWT, API key utilities
│   │   └── helpers.py          # General utilities
│   │
│   └── webhooks/               # Webhook system
│       ├── __init__.py
│       └── event_handler.py    # Webhook event handling
│
├── sdks/                       # Client libraries
│   ├── python_client.py        # Python SDK
│   └── client.ts               # Node.js/TypeScript SDK
│
├── tests/                      # Test files (to be implemented)
│
├── Dockerfile                  # Container image
├── docker-compose.yml          # Multi-container setup
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup script
│
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
│
├── README.md                   # Main documentation
├── API_DOCUMENTATION.md        # API reference
├── INTEGRATION_GUIDE.md        # Integration instructions
├── LICENSE                     # MIT License
│
└── [git, node_modules, venv]   # Auto-generated directories
```

## File Responsibilities

### Core Application (`src/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app setup, middleware, route inclusion |
| `config.py` | Settings management from environment |
| `database.py` | PostgreSQL connection and session management |
| `redis_client.py` | Redis client with caching interface |

### Database Models (`src/models/`)

| Model | Purpose |
|-------|---------|
| `Product` | Software products managed by users |
| `SKU` | Product tiers/plans with pricing and features |
| `License` | Issued licenses to customers |
| `ValidationToken` | Signed tokens for offline validation |
| `APIKey` | API authentication keys |
| `WebhookEvent` | Event log for webhooks |
| `AuditLog` | Audit trail of all operations |
| `RateLimitState` | Rate limit tracking per API key |

### Schemas (`src/schemas/`)

Pydantic models for:
- Request validation
- Response serialization
- OpenAPI documentation

### Services (`src/services/`)

Business logic implementation:
- **SKUService**: CRUD operations on SKUs
- **LicenseService**: License lifecycle (issue, activate, revoke, transfer)
- **ValidationEngine**: Fast license validation with caching

### Routes (`src/routes/`)

API endpoints grouped by resource:
- `/api/v1/health` - Health checks
- `/api/v1/products` - Product management
- `/api/v1/skus` - SKU management
- `/api/v1/licenses` - License management
- `/api/v1/validate` - License validation
- `/api/v1/api-keys` - API key management

### Middleware (`src/middleware/`)

Request processing:
- Authentication (JWT, API Key)
- Rate limiting
- CORS handling
- Request/response logging

## Architecture Patterns

### Service Layer Pattern
```
Routes (HTTP) → Services (Business Logic) → Models (Database)
```

### Repository Pattern (Implicit)
- Services act as repositories
- Queries encapsulated in service methods
- Database logic separated from API logic

### Dependency Injection
```python
@router.get("/licenses")
async def list_licenses(db: Session = Depends(get_db)):
    # db is injected by FastAPI
```

### Error Handling
- Exception handlers at application level
- Validation errors caught by Pydantic
- Custom HTTP exceptions for domain errors

## Data Flow Examples

### License Issuance Flow

```
1. POST /api/v1/licenses
   ↓
2. Route handler receives request
   ↓
3. Pydantic schema validates input
   ↓
4. Check product ownership
   ↓
5. LicenseService.issue_license(db, data)
   ↓
6. Generate license key
   ↓
7. Create License model instance
   ↓
8. Trigger webhook (license.issued)
   ↓
9. Return LicenseResponse to client
```

### License Validation Flow

```
1. POST /api/v1/validate
   ↓
2. Try offline validation with token
   ↓
3. If offline token valid, return cached response
   ↓
4. Else, fetch from database
   ↓
5. Check status (active/revoked/expired)
   ↓
6. Get SKU entitlements
   ↓
7. Cache response for 5 minutes
   ↓
8. Return ValidationResponse to client
```

## Key Design Decisions

### 1. Async/Await
- Used for I/O operations (database, Redis, webhooks)
- Non-blocking request handling
- Better resource utilization

### 2. Caching Strategy
- Validation responses cached for 5 minutes
- API key lookups cached
- Rate limit state in Redis
- Reduces database load

### 3. Authentication
- JWT for user/service authentication
- API keys for programmatic access
- Both supported simultaneously

### 4. Webhook Pattern
- Async webhook delivery
- Automatic retry with exponential backoff
- Signed payloads for security

### 5. Rate Limiting
- Per API key, not per user
- Implemented in middleware
- Redis-based for distributed counting

## Performance Considerations

### Database
- Connection pooling (20 default)
- Indexes on frequently queried columns
- UUID primary keys for distributed systems
- JSONB for flexible metadata

### Redis
- Sub-millisecond cache lookups
- Automatic expiration via TTL
- Pipeline operations for efficiency

### API Response Time
- Target: <100ms for validation
- Cached responses: <10ms
- Database queries optimized with indexes

## Security Features

### Authentication
- JWT token validation
- API key hashing (SHA-256)
- Clerk integration ready

### Authorization
- Per-user product isolation
- Permission-based API keys
- Request ownership verification

### Data Protection
- Sensitive data in environment variables
- Webhook signature verification
- Audit logging of all changes

### Input Validation
- Pydantic schema validation
- SQL injection prevention via ORM
- Rate limiting against abuse

## Testing Strategy (To Implement)

```
tests/
├── test_models.py           # ORM model tests
├── test_services.py         # Business logic tests
├── test_routes.py           # API endpoint tests
├── test_validation.py       # Validation engine tests
├── test_integration.py      # End-to-end tests
└── conftest.py              # Pytest fixtures
```

## Deployment Considerations

### Development
- SQLite or local PostgreSQL
- Redis localhost
- Debug mode enabled
- Auto-reload on file changes

### Staging
- PostgreSQL managed service
- Redis instance
- Debug mode disabled
- Staged releases

### Production
- PostgreSQL with replication
- Redis cluster
- Reverse proxy (Nginx)
- SSL/TLS certificates
- CloudFront/CDN for static content
- Health checks and monitoring

## Dependencies

### Core Framework
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Database
- **SQLAlchemy**: ORM
- **psycopg2**: PostgreSQL adapter
- **Alembic**: Migrations (optional)

### Authentication
- **PyJWT**: JWT handling
- **cryptography**: Encryption

### Caching & Events
- **Redis**: Cache and pub/sub
- **aioredis**: Async Redis client

### HTTP & External
- **httpx**: Async HTTP client
- **requests**: HTTP client

### Development
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

## Environment Variables

### Required
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `JWT_SECRET_KEY`: JWT signing key

### Optional
- `CLERK_PUBLISHABLE_KEY`: Clerk integration
- `CLERK_SECRET_KEY`: Clerk authentication
- `DEBUG`: Debug mode flag
- `ENVIRONMENT`: Environment name

See `.env.example` for full list.

## Common Tasks

### Start Development Server
```bash
source venv/bin/activate
python -m uvicorn src.main:app --reload
```

### Start with Docker
```bash
docker-compose up -d
```

### Run Tests
```bash
pytest
pytest tests/test_licenses.py -v
pytest --cov=src
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Check Code Quality
```bash
black src/
flake8 src/
mypy src/
```

---

**Last Updated**: January 15, 2024
**Version**: 1.0.0
**Status**: Production Ready
