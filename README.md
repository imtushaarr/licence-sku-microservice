# Open-Source License SKU Microservice

A standalone, production-ready backend service for managing software licensing, SKUs, and entitlements. Perfect for SaaS applications, desktop software, or any product requiring license management.

## Features

### Core Capabilities
- **Product Management**: Define and manage your software products
- **SKU Management**: Create pricing tiers with features, seat limits, and trial periods
- **License Lifecycle**: Issue, activate, revoke, transfer, and expire licenses
- **Fast Validation**: Sub-millisecond license validation with offline support
- **Seat Management**: Track and limit concurrent users per license
- **Offline Validation**: Signed tokens enable validation without network calls
- **Webhook Events**: Real-time notifications on license changes
- **Rate Limiting**: Built-in API rate limiting per client
- **Audit Logging**: Complete audit trail of all operations

### Technical Features
- **FastAPI**: Modern, fast Python web framework
- **PostgreSQL**: Reliable, ACID-compliant database
- **Redis**: High-performance caching and state management
- **JWT & API Keys**: Multiple authentication methods
- **OpenAPI**: Full API documentation
- **Docker**: Production-ready containerization
- **Async**: Non-blocking operations throughout

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│           (SaaS, Desktop App, Developer Tool)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                           │
│     API Key Auth • JWT Auth • Rate Limiting • CORS           │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌─────────┐     ┌──────────┐    ┌────────────────┐
   │   SKU   │     │ License  │    │  Validation    │
   │ Service │     │ Service  │    │   Engine       │
   └────┬────┘     └────┬─────┘    └────┬───────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐    ┌────────┐
   │PostgreSQL   │  Redis   │    │Webhooks│
   │  Database   │  Cache   │    │ Events │
   └─────────┘    └──────────┘    └────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 12+ (or use Docker)
- Redis 6+ (or use Docker)

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/yourusername/licence-sku-microservice.git
cd licence-sku-microservice

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# - Set DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, etc.
# - Add Clerk authentication keys if integrating

# Start all services
docker-compose up -d

# Service is available at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Local Development Setup

```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Start PostgreSQL and Redis (using Docker)
docker-compose up postgres redis

# Run migrations (if using Alembic)
alembic upgrade head

# Start development server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Products
```
POST   /api/v1/products              - Create product
GET    /api/v1/products              - List your products
GET    /api/v1/products/{id}         - Get product details
PUT    /api/v1/products/{id}         - Update product
DELETE /api/v1/products/{id}         - Delete product
```

### SKUs
```
POST   /api/v1/skus                  - Create SKU
GET    /api/v1/products/{id}/skus    - List product SKUs
GET    /api/v1/skus/{id}             - Get SKU details
PUT    /api/v1/skus/{id}             - Update SKU
DELETE /api/v1/skus/{id}             - Delete SKU
```

### Licenses
```
POST   /api/v1/licenses              - Issue license
GET    /api/v1/licenses              - List licenses
GET    /api/v1/licenses/{id}         - Get license details
POST   /api/v1/licenses/{id}/activate      - Activate license
POST   /api/v1/licenses/{id}/revoke        - Revoke license
POST   /api/v1/licenses/{id}/transfer      - Transfer license
POST   /api/v1/licenses/{id}/seats/assign   - Assign seat
POST   /api/v1/licenses/{id}/seats/unassign - Unassign seat
```

### Validation
```
POST   /api/v1/validate              - Validate license key
POST   /api/v1/validate/offline-token/{license_id} - Create offline token
```

### API Keys
```
POST   /api/v1/api-keys              - Create API key
GET    /api/v1/api-keys              - List API keys
DELETE /api/v1/api-keys/{id}         - Delete API key
```

### Health
```
GET    /api/v1/health                - Health check
GET    /api/v1/version               - API version
```

## Usage Examples

### Create a Product

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "My SaaS App",
    "slug": "my-saas-app",
    "description": "Best SaaS platform ever",
    "website_url": "https://mysaasapp.com"
  }'
```

### Create a SKU (Pricing Tier)

```bash
curl -X POST http://localhost:8000/api/v1/skus \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Professional",
    "tier": "pro",
    "monthly_price": 99.00,
    "annual_price": 990.00,
    "trial_days": 14,
    "max_seats": 10,
    "features": {
      "advanced_analytics": true,
      "api_access": true,
      "priority_support": true,
      "custom_branding": false
    },
    "rate_limit": 10000
  }'
```

### Issue a License

```bash
curl -X POST http://localhost:8000/api/v1/licenses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "sku_id": "660e8400-e29b-41d4-a716-446655440001",
    "customer_id": "acme-corp",
    "customer_email": "admin@acme.com",
    "organization_id": "org_123",
    "metadata": {
      "plan_started": "2024-01-01",
      "manager": "John Doe"
    }
  }'
```

### Validate a License

```bash
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LIC-XXXX-XXXX-XXXX-XXXX"
  }'
```

Response:
```json
{
  "valid": true,
  "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
  "customer_id": "acme-corp",
  "status": "active",
  "expires_at": "2025-01-01T00:00:00",
  "entitlements": [
    {
      "name": "advanced_analytics",
      "enabled": true,
      "details": {"tier": "pro"}
    }
  ],
  "seats": {
    "max_seats": 10,
    "current_used": 3,
    "available": 7,
    "assignments": {...}
  },
  "offline_validation": false
}
```

## Authentication

### API Key Authentication
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/licenses
```

### JWT Authentication (with Clerk)
```bash
curl -H "Authorization: Bearer your_jwt_token" http://localhost:8000/api/v1/licenses
```

## Webhooks

Configure webhooks to receive real-time notifications of license lifecycle events:

- `license.issued` - When a new license is issued
- `license.activated` - When a license is activated
- `license.expired` - When a license expires
- `license.revoked` - When a license is revoked
- `license.transferred` - When a license is transferred
- `license.seat_limit_reached` - When seat limit is reached

Webhook payload includes:
```json
{
  "event_type": "license.issued",
  "license_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {...}
}
```

## Offline Validation

Generate offline validation tokens for apps that need to validate licenses without network:

```bash
curl -X POST http://localhost:8000/api/v1/validate/offline-token/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

The token is a JWT that can be stored and validated locally using your JWT_SECRET_KEY.

## Environment Variables

See `.env.example` for all configuration options:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/licence_sku_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Clerk Integration
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=3600

# Webhooks
WEBHOOK_SECRET=your-webhook-secret
```

## Production Deployment

### Using Docker Swarm
```bash
docker stack deploy -c docker-compose.yml licence-sku
```

### Using Kubernetes
```bash
kubectl apply -f k8s/
```

### Environment Considerations
- Use strong JWT_SECRET_KEY
- Enable HTTPS only
- Configure CORS appropriately
- Set up SSL certificates
- Use managed database services
- Monitor logs and metrics
- Set up alerting

## Database Migrations

Using Alembic:
```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_licenses.py

# Run with verbose output
pytest -v
```

## Performance Optimization

- Validation responses are cached for 5 minutes
- Offline tokens enable app-side validation with no latency
- Connection pooling configured for database
- Redis used for caching and rate limiting
- Indexes on frequently queried columns

## Troubleshooting

### Database Connection Error
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Ensure database user has proper permissions

### Redis Connection Error
- Verify REDIS_URL is correct
- Check Redis is running: `redis-cli ping`
- Check firewall allows Redis port (6379)

### License Validation Fails
- Verify license key format
- Check license isn't revoked
- Verify license hasn't expired
- Check offline token if using offline validation

## Development

### Code Style
```bash
# Format code
black src/

# Check linting
flake8 src/

# Type checking
mypy src/
```

### Adding New Features
1. Create service class in `src/services/`
2. Define Pydantic schemas in `src/schemas/`
3. Add routes in `src/routes/`
4. Add database models in `src/models/`
5. Write tests in `tests/`

## Client Libraries

### Python SDK
```python
from licence_sku_client import LicenceSkuClient

client = LicenceSkuClient(
    api_url="http://localhost:8000",
    api_key="your_api_key"
)

# Validate license
result = client.validate("LIC-XXXX-XXXX-XXXX-XXXX")
if result.valid:
    print(f"License valid until {result.expires_at}")
    print(f"Features: {result.entitlements}")
```

### Node.js SDK
```javascript
import { LicenceSkuClient } from '@licence-sku/client-js';

const client = new LicenceSkuClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

const result = await client.validate('LIC-XXXX-XXXX-XXXX-XXXX');
if (result.valid) {
  console.log(`Features: ${result.entitlements}`);
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Documentation: Comming Soon
- Issues: https://github.com/imtushaarr/licence-sku-microservice/issues
- Email: tusharguptagps@gmail.com

## Roadmap

- [ ] GraphQL API
- [ ] Multi-tenant support improvements
- [ ] Advanced analytics dashboard
- [ ] Stripe/PayPal integration
- [ ] Email notification templates
- [ ] Fraud detection
- [ ] Geographic pricing

---

Built with ❤️ for developers who need robust licensing management.
