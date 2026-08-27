# Sentinel Hub Authentication

This tool requires OAuth2 credentials to query the Sentinel Hub Catalog API.

## Getting Credentials

### Step 1: Create OAuth Client

1. Log in to https://dataspace.copernicus.eu/dashboard
2. Go to **User Settings** → **OAuth clients**
3. Click **Create** and give your client a name
4. Choose an expiry date (or "Never expire")
5. Click **Create** and save your credentials:
   - **Client ID**
   - **Client Secret**

### Step 2: Set Environment Variables

Export the environment variables
```bash
export SH_CLIENT_ID="your-client-id"
export SH_CLIENT_SECRET="your-client-secret"
```

Or create a `.env` file:
```
SH_CLIENT_ID=your-client-id
SH_CLIENT_SECRET=your-client-secret
```
and let the tool load them for you when running `python main.py`

## How It Works

1. Tool sends client credentials to OAuth2 endpoint
2. Endpoint returns an access token (JWT)
3. Token is included in API requests
4. Token expires after a period (check expiration in JWT)
5. Tool automatically re-authenticates when token expires

**Endpoint**: `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`

## Programmatic Use

```python
from sh_catalog import SentinelHubCatalog

# Option 1: From environment variables
catalog = SentinelHubCatalog()

# Option 2: Pass credentials directly
catalog = SentinelHubCatalog(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Fetch collections
collections = catalog.fetch_collections({"4046945c", "bd02588b"})
```

## Troubleshooting

### "Authentication failed: 401"
- Verify Client ID and Client Secret are correct
- Check that the OAuth client is still active
- Ensure credentials are for CDSE (not original Sentinel Hub)

### "Authentication failed: 400"
- Might be malformed request
- Check that credentials don't have leading/trailing spaces
- Verify grant_type is "client_credentials"

### "Connection timeout"
- Check internet connection
- Verify OAuth endpoint is accessible: `https://identity.dataspace.copernicus.eu/`

## Security Best Practices

- ⚠️ **Never commit credentials to git**
- Use environment variables or secure vaults
- Rotate credentials periodically
- Use separate clients for different services
- Monitor OAuth client usage in dashboard

## References

- OAuth Client Management: https://dataspace.copernicus.eu/dashboard
- API Documentation: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html
