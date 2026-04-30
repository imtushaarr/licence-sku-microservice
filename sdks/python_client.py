"""Python SDK for License SKU Microservice."""

import requests
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LicenceSkuClient:
    """Python client for License SKU Microservice."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 10,
    ):
        """Initialize client.
        
        Args:
            api_url: Base URL of the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def validate_license(self, license_key: str, offline_token: Optional[str] = None) -> Dict[str, Any]:
        """Validate a license key.
        
        Args:
            license_key: License key to validate
            offline_token: Optional offline validation token
            
        Returns:
            Validation response with entitlements and status
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/validate"
        payload = {
            "license_key": license_key,
            "offline_token": offline_token,
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def create_license(
        self,
        product_id: str,
        sku_id: str,
        customer_id: str,
        customer_email: str,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Issue a new license.
        
        Args:
            product_id: Product UUID
            sku_id: SKU UUID
            customer_id: Customer identifier
            customer_email: Customer email
            organization_id: Optional organization ID
            metadata: Optional metadata
            
        Returns:
            Created license details
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/licenses"
        payload = {
            "product_id": product_id,
            "sku_id": sku_id,
            "customer_id": customer_id,
            "customer_email": customer_email,
            "organization_id": organization_id,
            "metadata": metadata,
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def revoke_license(self, license_id: str, reason: str) -> Dict[str, Any]:
        """Revoke a license.
        
        Args:
            license_id: License ID
            reason: Revocation reason
            
        Returns:
            Updated license details
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/licenses/{license_id}/revoke"
        payload = {"reason": reason}
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def transfer_license(
        self,
        license_id: str,
        new_customer_id: str,
        new_customer_email: str,
    ) -> Dict[str, Any]:
        """Transfer a license to another user.
        
        Args:
            license_id: License ID
            new_customer_id: New customer ID
            new_customer_email: New customer email
            
        Returns:
            Updated license details
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/licenses/{license_id}/transfer"
        payload = {
            "new_customer_id": new_customer_id,
            "new_customer_email": new_customer_email,
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def assign_seat(self, license_id: str, email: str) -> Dict[str, Any]:
        """Assign a seat to a user.
        
        Args:
            license_id: License ID
            email: User email
            
        Returns:
            Response with success status
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/licenses/{license_id}/seats/assign"
        payload = {"email": email}
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def unassign_seat(self, license_id: str, email: str) -> Dict[str, Any]:
        """Unassign a seat from a user.
        
        Args:
            license_id: License ID
            email: User email
            
        Returns:
            Response with success status
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/licenses/{license_id}/seats/unassign"
        payload = {"email": email}
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_offline_token(self, license_id: str) -> str:
        """Get offline validation token for a license.
        
        Args:
            license_id: License ID
            
        Returns:
            JWT token for offline validation
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/validate/offline-token/{license_id}"
        
        response = self.session.post(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("token")

    def health_check(self) -> Dict[str, Any]:
        """Check service health.
        
        Returns:
            Health check response
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.api_url}/api/v1/health"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
