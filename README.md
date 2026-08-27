# CLMS Collections Status in CDSE Sentinel Hub

Extract BYOC collection IDs from EU-CDSE documentation and verify their availability in Sentinel Hub. Generates report in CSV format.

## What It Does

1. **Extracts** BYOC collection IDs from `.qmd` documentation files on GitHub
2. **Queries** Sentinel Hub Catalog API to verify collection availability
3. **Exports** results to CSV

## Quick Start

### Prerequisites
- **Python** >= 3.12
- CDSE SH Auth credentials

### Installation

**Using pip:**
```bash
# Clone or navigate to the project directory
cd SH-CLMS-Status

# Create a virtual environment
python3.12 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package and dependencies
pip install -e .
```

**Using `uv`** (optional, if preferred):
```bash
cd SH-CLMS-Status
uv sync
```

### Authentication

The Sentinel Hub Catalog API requires OAuth2 credentials. See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed setup instructions.

**Default setup:**
Follow the steps to get your auth credentials and write them to an `.env` file:
```
SH_CLIENT_ID=your-client-id
SH_CLIENT_SECRET=your-client-secret
```
When you run the tool from the `main.py` entry point, it will automatically load the credentials as environment variables.

### Run the Tool

**Silent mode** - no output, generates CSV file:
```bash
python main.py
```
Output: `CLMS_SH_collection_status.csv` with collection data

**Info mode** - shows INFO-level logs and generates CSV:
```bash
python main.py --log-level info
# or
python main.py -l info
```

**Debug mode** - shows DEBUG-level logs and generates CSV:
```bash
python main.py --log-level debug
# or
python main.py -l debug
```

### CSV Export

The tool automatically creates `CLMS_SH_collection_status.csv` with the following columns:
- **BYOC ID**: Collection identifier with `byoc-` prefix
- **Name**: Human-readable collection name
- **Available**: "True" if found in CDSE, "False" if not
- **Last Updated**: ISO timestamp when the file was generated

Example:
```csv
BYOC ID,Name,Available,Last Updated
byoc-64d015da-e225-48d8-9643-30a453657beb,Cloud Classification Europe,Yes,2026-08-27T10:15:30.123456
byoc-4046945c,LAI global 300m 10-daily v2,Yes,2026-08-27T10:15:30.123456
byoc-invalid-id,Unknown,No,2026-08-27T10:15:30.123456
```

### Logging

The tool uses Python's standard `logging` module with three modes:

| Mode | Command | Output |
|------|---------|--------|
| **Silent** | `python main.py` | No logging (just CSV file) |
| **Info** | `python main.py -l info` | Main processing steps only |
| **Debug** | `python main.py -l debug` | Detailed logs with individual IDs |

Example info output:
```
INFO     | id_extractor | Fetching repository tree...
INFO     | id_extractor | Found 186 .qmd files in eu-cdse/documentation/tree/publish/APIs/SentinelHub/Data/clms
INFO     | sh_catalog | Querying Sentinel Hub Catalog API for 186 collections
INFO     | sh_catalog | Available in CDSE: 150
INFO     | sh_catalog | Not found in CDSE: 36
```

Example debug output (includes info + detailed lines):
```
DEBUG    | id_extractor | ✓ bio-geophysical-parameters/auxiliary-data/cloud-mask/clms_wsi_cloud-classification_europe_utm_20m_daily_v1.qmd
DEBUG    | id_extractor |   └─ 64d015da-e225-48d8-9643-30a453657beb
DEBUG    | sh_catalog | Querying Sentinel Hub Catalog API for 186 collections
DEBUG    | sh_catalog | Unavailable IDs: ['id1', 'id2', ...]
```

## Architecture

### Modules

**`id_extractor.py`** - Extracts collection IDs from GitHub documentation
- Fetches repository tree with single API call (no rate limits on file downloads)
- Parses `.qmd` files for UUID collection IDs in ````default <UUID>```` code blocks
- UUID format: `8-4-4-4-12` (e.g., `64d015da-e225-48d8-9643-30a453657beb`)
- Returns set of unique collection IDs

**`sh_catalog.py`** - Queries Sentinel Hub Catalog API
- Endpoint: `https://sh.dataspace.copernicus.eu/catalog/v1/collections`
- Verifies collection availability in CDSE
- Adds `byoc-` prefix automatically (required for BYOC collections)
- Returns collection metadata

**`main.py`** - Entry point and orchestrator
- Handles command-line argument parsing
- Combines extraction and verification
- Saves results to CSV file

## Project Structure

```
.
├── main.py                  # Entry point - CLI interface
├── src/
│   ├── __init__.py          # Package initialization
│   ├── id_extractor.py      # GitHub documentation parser
│   └── sh_catalog.py        # Sentinel Hub Catalog API client
├── pyproject.toml           # Project configuration
├── README.md                # Documentation
├── AUTHENTICATION.md        # OAuth setup guide
```

## Important Notes

### GitHub API Rate Limiting

⚠️ **Current behavior**: The tool makes **unauthenticated GitHub API requests**, which are limited to **60 requests/hour**.

For the CLMS documentation extraction, this typically means:
- 1 request to fetch the repository tree
- Individual file fetches from `raw.githubusercontent.com` (no rate limit)

**You will hit the rate limit if**:
- You run the tool more than 60 times per hour
- You increase the scope to other repositories with many files
- GitHub is processing your account's other API requests

### How to Add GitHub Authentication

To increase the rate limit to **5,000 requests/hour**, extend the code with a personal access token:

```python
# In id_extractor.py, modify fetch_repository_tree():

def fetch_repository_tree(self) -> list[dict] | None:
    """Fetch entire repository tree in one API call with recursive=1."""
    url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/git/trees/{self.branch}?recursive=1"
    
    # Add GitHub token authentication
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        # ... rest of the code
```

Then set your token:
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
python main.py
```

**To create a GitHub token**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: `public_repo` (read-only access to public repos)
4. Copy the token and save it securely

See [GitHub API Authentication](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api) for details.

## Troubleshooting

### GitHub API Rate Limit Exceeded
**Error**: `403 Client Error: rate limit exceeded`

**Causes**:
- Made too many API calls in the last hour
- Rate limit resets every hour

**Solutions**:
1. Wait 1 hour for rate limit to reset
2. Use GitHub authentication token (increases limit to 5000/hour)
3. Check current rate limit status: `https://api.github.com/rate_limit`

### Collection Not Found in CDSE
**Problem**: A collection ID from documentation doesn't exist in Sentinel Hub

**Possible reasons**:
- Collection is not registered in CDSE (may be in original Sentinel Hub)
- Collection ID is incorrect or deprecated
- Collection is temporarily unavailable

**How to check**:
```python
from src.sh_catalog import SentinelHubCatalog

catalog = SentinelHubCatalog()
result = catalog.get_collection("4046945c")
if result is None:
    print("Collection not found in CDSE")
```

### Empty Results
**Problem**: No collection IDs are extracted

**Check**:
1. Internet connection is working
2. GitHub repository is accessible: https://github.com/eu-cdse/documentation
3. Target path exists: `APIs/SentinelHub/Data/clms`
4. `.qmd` files contain the ID pattern: ````default <ID>````

### Authentication Failed
**Error**: `❌ Authentication failed: 401` or similar

**Solutions**:
1. Verify credentials are correct: `SH_CLIENT_ID` and `SH_CLIENT_SECRET`
2. Check that credentials are for Copernicus Data Space Ecosystem (not original Sentinel Hub)
3. Credentials must have "OAuth 2.0" capability enabled
4. If credentials expired, generate new ones at https://dataspace.copernicus.eu/

