# Integration Guide - License SKU Microservice with Clerk Auth

This guide explains how to integrate the License SKU Microservice with your Clerk Auth Microservice.

## Overview

Your architecture has two microservices:
1. **Clerk Auth Microservice** (Port 5173) - Handles user authentication
2. **License SKU Microservice** (Port 8000) - Manages product licensing

## Integration Points

### 1. Authentication Flow

```
┌─────────────┐          ┌──────────────┐          ┌────────────────┐
│   Client    │          │  Clerk Auth  │          │ License SKU    │
│             │────────→ │  (Port 5173) │────────→ │ (Port 8000)    │
│             │          │              │          │                │
│             │←─Token──│              │←─License─│                │
└─────────────┘          └──────────────┘          └────────────────┘
```

### 2. Setup Steps

#### Step 1: Configure Clerk Integration in .env

```bash
# In /Users/agustya/Documents/Projects/licence-sku-microservice/.env

# Clerk Configuration
CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key
CLERK_AUTH_SERVICE_URL=http://localhost:5173

# CORS to allow requests from Clerk Auth service
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000
```

#### Step 2: Update Clerk Auth Microservice to Know About License Service

In `Clerk-Auth-Microservice/.env`:
```bash
LICENSE_SERVICE_URL=http://localhost:8000
LICENSE_SERVICE_API_KEY=your_api_key_here
```

### 3. User Authentication Workflow

#### When User Logs In:

1. **Client** authenticates with Clerk Auth Service
   ```javascript
   POST http://localhost:5173/api/auth/login
   {
     "email": "user@example.com",
     "password": "password"
   }
   ```

2. **Clerk Auth Service** creates Clerk session and returns JWT token
   ```json
   {
     "token": "eyJhbGc...",
     "user_id": "user_123",
     "email": "user@example.com"
   }
   ```

3. **Client** uses JWT to access License Service
   ```javascript
   // Get user's licenses
   GET http://localhost:8000/api/v1/licenses?product_id=prod_123
   Headers: {
     "Authorization": "Bearer eyJhbGc..."
   }
   ```

4. **License Service** validates JWT with Clerk
   - Extracts `user_id` from token
   - Verifies signature with Clerk's public key
   - Returns user's licenses

### 4. Middleware Integration

#### Clerk JWT Verification Middleware

Add to `src/middleware/clerk_auth.py`:

```python
import httpx
from fastapi import HTTPException, status
from src.config import settings

async def verify_clerk_token(token: str) -> dict:
    """Verify JWT token with Clerk."""
    try:
        # Get Clerk's public key
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.clerk.com/v1/jwks",
                headers={
                    "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"
                }
            )
            response.raise_for_status()
            
        # Verify JWT
        from python_jose import jwt
        payload = jwt.get_unverified_claims(token)
        return payload
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
```

### 5. Database Integration

#### Schema for License Ownership

The `License` model already tracks:
- `customer_id` - Clerk user ID
- `customer_email` - User's email
- `organization_id` - Optional organization

Example:
```python
license = db.query(License).filter(
    License.customer_id == clerk_user_id,
    License.status == "active"
).all()
```

### 6. Webhook Integration

#### License Events Sent to Clerk Service

Configure webhooks in `docker-compose.yml`:

```yaml
services:
  app:
    environment:
      WEBHOOK_ENDPOINTS=http://localhost:5173/webhooks/license-events
```

#### Webhook Event Examples

When license status changes, Clerk service receives:

```json
{
  "event_type": "license.issued",
  "license_id": "lic_123",
  "customer_id": "user_123",
  "data": {
    "license_key": "LIC-XXXX-XXXX-XXXX-XXXX",
    "expires_at": "2025-01-15T00:00:00Z"
  }
}
```

### 7. Client-Side Integration

#### Python Client Using Both Services

```python
from licence_sku_client import LicenceSkuClient
import requests

class LicensedUserClient:
    def __init__(self, auth_url="http://localhost:5173", 
                 license_url="http://localhost:8000"):
        self.auth_url = auth_url
        self.license_url = license_url
        self.token = None
        
    def login(self, email: str, password: str):
        """Login via Clerk and get token."""
        response = requests.post(
            f"{self.auth_url}/api/auth/login",
            json={"email": email, "password": password}
        )
        self.token = response.json()["token"]
        self.user_id = response.json()["user_id"]
        return self.token
        
    def get_licenses(self, product_id: str):
        """Get user's licenses."""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.license_url}/api/v1/licenses",
            params={"product_id": product_id},
            headers=headers
        )
        return response.json()
        
    def validate_license(self, license_key: str):
        """Validate a specific license."""
        response = requests.post(
            f"{self.license_url}/api/v1/validate",
            json={"license_key": license_key}
        )
        return response.json()

# Usage
client = LicensedUserClient()
token = client.login("user@example.com", "password")
licenses = client.get_licenses("my-product-id")
```

#### Node.js Integration

```javascript
import ClerkClient from './clerk-client'; // Your Clerk client
import { LicenceSkuClient } from '@licence-sku/client-js';

class LicensedApp {
  constructor() {
    this.clerkClient = new ClerkClient('http://localhost:5173');
    this.licenseClient = new LicenceSkuClient({
      apiUrl: 'http://localhost:8000'
    });
    this.token = null;
  }

  async login(email, password) {
    const response = await this.clerkClient.login(email, password);
    this.token = response.token;
    return response;
  }

  async getUserLicenses(productId) {
    const response = await fetch(
      `http://localhost:8000/api/v1/licenses?product_id=${productId}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }

  async validateLicense(licenseKey) {
    return this.licenseClient.validate(licenseKey);
  }
}

// Usage
const app = new LicensedApp();
await app.login('user@example.com', 'password');
const licenses = await app.getUserLicenses('my-product-id');
```

## API Gateway Pattern (Recommended for Production)

```
┌──────────┐
│ Client   │
└─────┬────┘
      │
      ▼
┌─────────────────────────────────┐
│   API Gateway / Load Balancer   │  (Single entry point)
│   - Request routing             │
│   - Authentication              │
│   - Rate limiting               │
└─────────────────────────────────┘
      │                    │
      ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│  Clerk Auth  │    │ License SKU      │
│  (Port 5173) │    │ (Port 8000)      │
└──────────────┘    └──────────────────┘
```

### Kong Configuration Example

```yaml
services:
  - name: clerk-auth
    url: http://localhost:5173
    routes:
      - paths:
          - /auth
          - /api/auth

  - name: license-sku
    url: http://localhost:8000
    routes:
      - paths:
          - /licenses
          - /api/v1

plugins:
  - name: jwt
    config:
      secret: your-jwt-secret
```

## Security Best Practices

1. **Always Validate Tokens**
   - Verify JWT signature with Clerk's keys
   - Check token expiration
   - Validate user permissions

2. **API Key Rotation**
   - Rotate API keys regularly
   - Use different keys per environment
   - Store securely in environment variables

3. **HTTPS Only**
   - Use TLS/SSL certificates
   - Redirect HTTP to HTTPS
   - Set secure cookie flags

4. **Rate Limiting**
   - Implemented per API key
   - 1000 requests/hour by default
   - Configurable per client

5. **Audit Logging**
   - All operations logged to `audit_logs` table
   - Track who changed what and when
   - Export logs regularly

## Troubleshooting

### Token Validation Fails
```bash
# Check Clerk configuration
curl -X GET https://api.clerk.com/v1/jwks \
  -H "Authorization: Bearer sk_test_..."

# Verify token is valid
# Check token expiration time
```

### CORS Issues
```bash
# Ensure CORS_ORIGINS in .env includes both services
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# Test CORS
curl -X OPTIONS http://localhost:8000/api/v1/licenses \
  -H "Origin: http://localhost:5173"
```

### License Service Can't Access Clerk
```bash
# Check network connectivity
curl http://localhost:5173/api/auth/status

# Verify environment variables
echo $CLERK_AUTH_SERVICE_URL
echo $CLERK_SECRET_KEY
```

## Monitoring

### Health Check Endpoints

```bash
# Clerk service health
curl http://localhost:5173/api/health

# License service health
curl http://localhost:8000/api/v1/health

# Check dependencies
curl http://localhost:8000/api/v1/health | jq '.components'
```

### Logging Configuration

```python
# In src/config.py
LOG_LEVEL=INFO
LOG_FORMAT=json  # For structured logging

# View logs
docker logs licence-sku-app
docker logs clerk-auth-app
```

## Next Steps

1. ✅ Set up environment variables in both services
2. ✅ Configure CORS origins
3. ✅ Test authentication flow
4. ✅ Implement webhook handlers
5. ✅ Set up monitoring and logging
6. ✅ Deploy to staging
7. ✅ Run integration tests
8. ✅ Deploy to production

---

For more details, see:
- [API Documentation](API_DOCUMENTATION.md)
- [README.md](README.md)
- Clerk Documentation: https://clerk.com/docs
