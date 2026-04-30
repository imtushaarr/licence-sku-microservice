// Node.js/JavaScript SDK for License SKU Microservice
// Example client implementation for Node.js/TypeScript

export interface ValidationResponse {
  valid: boolean;
  license_key: string;
  customer_id: string;
  status: 'active' | 'expired' | 'revoked' | 'suspended';
  expires_at?: string;
  entitlements: Entitlement[];
  seats?: SeatInfo;
  offline_validation: boolean;
}

export interface Entitlement {
  name: string;
  enabled: boolean;
  details?: Record<string, any>;
}

export interface SeatInfo {
  max_seats?: number;
  current_used: number;
  available?: number;
  assignments: Record<string, string>;
}

export interface LicenseData {
  id: string;
  license_key: string;
  product_id: string;
  sku_id: string;
  customer_id: string;
  customer_email: string;
  status: string;
  issued_at: string;
  expires_at?: string;
}

export class LicenceSkuClient {
  private apiUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(options: {
    apiUrl?: string;
    apiKey?: string;
    timeout?: number;
  } = {}) {
    this.apiUrl = (options.apiUrl || 'http://localhost:8000').replace(/\/$/, '');
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 10000;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T> {
    const url = `${this.apiUrl}/api/v1${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API Error: ${error.message || response.statusText}`);
    }

    return response.json();
  }

  async validate(licenseKey: string, offlineToken?: string): Promise<ValidationResponse> {
    return this.request<ValidationResponse>('POST', '/validate', {
      license_key: licenseKey,
      offline_token: offlineToken,
    });
  }

  async createLicense(data: {
    product_id: string;
    sku_id: string;
    customer_id: string;
    customer_email: string;
    organization_id?: string;
    metadata?: Record<string, any>;
  }): Promise<LicenseData> {
    return this.request<LicenseData>('POST', '/licenses', data);
  }

  async revokeLicense(licenseId: string, reason: string): Promise<LicenseData> {
    return this.request<LicenseData>('POST', `/licenses/${licenseId}/revoke`, {
      reason,
    });
  }

  async transferLicense(
    licenseId: string,
    newCustomerId: string,
    newCustomerEmail: string
  ): Promise<LicenseData> {
    return this.request<LicenseData>('POST', `/licenses/${licenseId}/transfer`, {
      new_customer_id: newCustomerId,
      new_customer_email: newCustomerEmail,
    });
  }

  async assignSeat(licenseId: string, email: string): Promise<any> {
    return this.request('POST', `/licenses/${licenseId}/seats/assign`, {
      email,
    });
  }

  async unassignSeat(licenseId: string, email: string): Promise<any> {
    return this.request('POST', `/licenses/${licenseId}/seats/unassign`, {
      email,
    });
  }

  async getOfflineToken(licenseId: string): Promise<string> {
    const response = await this.request<{ token: string }>(
      'POST',
      `/validate/offline-token/${licenseId}`
    );
    return response.token;
  }

  async healthCheck(): Promise<any> {
    return this.request('GET', '/health');
  }
}

// Export as default
export default LicenceSkuClient;
