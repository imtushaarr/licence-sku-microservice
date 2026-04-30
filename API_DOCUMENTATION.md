"""
API_DOCUMENTATION.md - License SKU Microservice API Reference

Complete API documentation for integrating with the License SKU Microservice.
"""

# License SKU Microservice - API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### API Key Authentication
Include API key in request header:
```
X-API-Key: your_api_key_here
```

### JWT Authentication (with Clerk)
Include JWT token in Authorization header:
```
Authorization: Bearer your_jwt_token_here
```

---

## Health & Status

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### Version Information
```
GET /version
```

---

## Products

### Create Product
```
POST /products
Content-Type: application/json
Authorization: Bearer token

{
  "name": "My SaaS App",
  "slug": "my-saas-app",
  "description": "Best SaaS platform",
  "logo_url": "https://example.com/logo.png",
  "website_url": "https://example.com"
}
```

Response (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My SaaS App",
  "slug": "my-saas-app",
  "description": "Best SaaS platform",
  "logo_url": "https://example.com/logo.png",
  "website_url": "https://example.com",
  "created_by": "user_123",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

### List Products
```
GET /products?skip=0&limit=20
Authorization: Bearer token
```

### Get Product
```
GET /products/{product_id}
Authorization: Bearer token
```

### Update Product
```
PUT /products/{product_id}
Content-Type: application/json
Authorization: Bearer token

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Product
```
DELETE /products/{product_id}
Authorization: Bearer token
```

---

## SKUs (Stock Keeping Units)

### Create SKU
```
POST /skus
Content-Type: application/json
Authorization: Bearer token

{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Professional Plan",
  "tier": "pro",
  "description": "Best for growing teams",
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
  "rate_limit": 10000,
  "storage_gb": 100
}
```

Response (201):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Professional Plan",
  "tier": "pro",
  "description": "Best for growing teams",
  "monthly_price": 99.00,
  "annual_price": 990.00,
  "trial_days": 14,
  "max_seats": 10,
  "features": {...},
  "rate_limit": 10000,
  "storage_gb": 100,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### List Product SKUs
```
GET /products/{product_id}/skus?skip=0&limit=20
Authorization: Bearer token
```

### Get SKU
```
GET /skus/{sku_id}
```

### Update SKU
```
PUT /skus/{sku_id}
Content-Type: application/json
Authorization: Bearer token

{
  "monthly_price": 109.00,
  "max_seats": 15
}
```

### Delete SKU
```
DELETE /skus/{sku_id}
Authorization: Bearer token
```

---

## Licenses

### Issue License
```
POST /licenses
Content-Type: application/json
Authorization: Bearer token

{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "sku_id": "660e8400-e29b-41d4-a716-446655440001",
  "customer_id": "acme-corp",
  "customer_email": "admin@acme.com",
  "organization_id": "org_123",
  "metadata": {
    "plan_started": "2024-01-01",
    "manager": "John Doe"
  },
  "notes": "Enterprise agreement"
}
```

Response (201):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "sku_id": "660e8400-e29b-41d4-a716-446655440001",
  "customer_id": "acme-corp",
  "customer_email": "admin@acme.com",
  "organization_id": "org_123",
  "status": "active",
  "issued_at": "2024-01-15T10:30:00Z",
  "activated_at": null,
  "expires_at": "2024-02-15T10:30:00Z",
  "current_seats_used": 0,
  "seat_assignments": {},
  "metadata": {...}
}
```

### List Licenses
```
GET /licenses?product_id=550e8400-e29b-41d4-a716-446655440000&skip=0&limit=20&status=active
Authorization: Bearer token
```

Response:
```json
{
  "total": 150,
  "page": 0,
  "page_size": 20,
  "items": [...]
}
```

### Get License
```
GET /licenses/{license_id}
Authorization: Bearer token
```

### Activate License
```
POST /licenses/{license_id}/activate
Authorization: Bearer token
```

### Revoke License
```
POST /licenses/{license_id}/revoke
Content-Type: application/json
Authorization: Bearer token

{
  "reason": "Customer requested cancellation"
}
```

### Transfer License
```
POST /licenses/{license_id}/transfer
Content-Type: application/json
Authorization: Bearer token

{
  "new_customer_id": "new-corp",
  "new_customer_email": "newadmin@newcorp.com"
}
```

### Assign Seat
```
POST /licenses/{license_id}/seats/assign
Content-Type: application/json
Authorization: Bearer token

{
  "email": "john.doe@acme.com"
}
```

Response:
```json
{
  "success": true,
  "message": "Seat assigned to john.doe@acme.com"
}
```

### Unassign Seat
```
POST /licenses/{license_id}/seats/unassign
Content-Type: application/json
Authorization: Bearer token

{
  "email": "john.doe@acme.com"
}
```

---

## Validation

### Validate License
```
POST /validate
Content-Type: application/json

{
  "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
  "offline_token": null
}
```

Response (Valid):
```json
{
  "valid": true,
  "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
  "customer_id": "acme-corp",
  "status": "active",
  "expires_at": "2024-02-15T10:30:00Z",
  "entitlements": [
    {
      "name": "advanced_analytics",
      "enabled": true,
      "details": {"tier": "pro"}
    },
    {
      "name": "api_access",
      "enabled": true,
      "details": {"tier": "pro"}
    }
  ],
  "seats": {
    "max_seats": 10,
    "current_used": 3,
    "available": 7,
    "assignments": {
      "john@acme.com": "2024-01-15T10:30:00Z",
      "jane@acme.com": "2024-01-16T14:22:00Z"
    }
  },
  "offline_validation": false
}
```

Response (Invalid):
```json
{
  "valid": false,
  "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
  "customer_id": "unknown",
  "status": "revoked",
  "message": "License revoked: Customer requested cancellation",
  "entitlements": [],
  "offline_validation": false
}
```

### Create Offline Token
```
POST /validate/offline-token/{license_id}
Authorization: Bearer token
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "token_type": "offline_validation"
}
```

---

## API Keys

### Create API Key
```
POST /api-keys
Content-Type: application/json
Authorization: Bearer token

{
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Key",
  "description": "API key for production environment",
  "permissions": {
    "resources": ["licenses", "skus"],
    "actions": ["read", "write"]
  }
}
```

Response (201):
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "product_id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "sk_live_xxxxxxxxxxxxxxxxxxxx",
  "name": "Production Key",
  "description": "API key for production environment",
  "permissions": {...},
  "is_active": true,
  "last_used_at": null,
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": null
}
```

### List API Keys
```
GET /api-keys?product_id=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer token
```

### Delete API Key
```
DELETE /api-keys/{api_key_id}
Authorization: Bearer token
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "details": [
    {
      "field": "monthly_price",
      "message": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid authentication"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Not authorized to manage this resource"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

Rate limits are enforced per API key:
- Default: 1000 requests per hour
- Headers returned with each response:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Webhooks

Register webhook endpoints in your product settings. Events include:
- `license.issued`
- `license.activated`
- `license.expired`
- `license.revoked`
- `license.transferred`
- `license.seat_limit_reached`

Webhook payload:
```json
{
  "event_type": "license.issued",
  "license_id": "770e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
    "customer_id": "acme-corp",
    "customer_email": "admin@acme.com"
  }
}
```

All webhooks include signature header:
```
X-Webhook-Signature: sha256_hash_of_payload
```

---

## Best Practices

1. **Always validate licenses** - Call `/validate` before granting access
2. **Cache validation results** - Results are cached server-side for 5 minutes
3. **Use offline tokens** - For offline apps, generate tokens for background validation
4. **Handle errors gracefully** - Implement retry logic with exponential backoff
5. **Secure your API keys** - Rotate keys regularly, use environment variables
6. **Monitor rate limits** - Implement logic to slow down if approaching limits
7. **Test in sandbox** - Use test API keys before going live
8. **Log webhook events** - Keep audit trail of license changes

---

## Code Examples

### Python
```python
from licence_sku_client import LicenceSkuClient

client = LicenceSkuClient(
    api_url="http://localhost:8000",
    api_key="your_api_key"
)

# Validate license
result = client.validate_license("LIC-XXXX-XXXX-XXXX-XXXX")
if result['valid']:
    print(f"License valid until {result['expires_at']}")
    print(f"Features: {result['entitlements']}")

# Create license
license = client.create_license(
    product_id="550e8400-e29b-41d4-a716-446655440000",
    sku_id="660e8400-e29b-41d4-a716-446655440001",
    customer_id="acme-corp",
    customer_email="admin@acme.com"
)
print(f"License created: {license['license_key']}")
```

### Node.js
```javascript
import LicenceSkuClient from '@licence-sku/client-js';

const client = new LicenceSkuClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// Validate license
const result = await client.validate('LIC-XXXX-XXXX-XXXX-XXXX');
if (result.valid) {
  console.log(`License valid until ${result.expires_at}`);
  console.log(`Features: ${JSON.stringify(result.entitlements)}`);
}

// Create license
const license = await client.createLicense({
  product_id: '550e8400-e29b-41d4-a716-446655440000',
  sku_id: '660e8400-e29b-41d4-a716-446655440001',
  customer_id: 'acme-corp',
  customer_email: 'admin@acme.com'
});
console.log(`License created: ${license.license_key}`);
```

### cURL
```bash
# Create license
curl -X POST http://localhost:8000/api/v1/licenses \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "sku_id": "660e8400-e29b-41d4-a716-446655440001",
    "customer_id": "acme-corp",
    "customer_email": "admin@acme.com"
  }'

# Validate license
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LIC-XXXX-XXXX-XXXX-XXXX"
  }'
```

---

Last Updated: January 15, 2024
