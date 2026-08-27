"""Module for querying the Sentinel Hub Catalog API for BYOC collection information."""

import logging
import os
from typing import Any

import requests
from requests.models import Response

logger: logging.Logger = logging.getLogger(__name__)


class SentinelHubCatalog:
    """Query Sentinel Hub Catalog API for collection information."""

    def __init__(
        self,
        base_url: str = "https://sh.dataspace.copernicus.eu",
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.base_url: str = base_url
        self.collections: dict[str, dict] = {}
        self.access_token: str | None = None

        # Get credentials from parameters or environment variables
        self.client_id: str | None = client_id or os.getenv("SH_CLIENT_ID")
        self.client_secret: str | None = client_secret or os.getenv("SH_CLIENT_SECRET")

        # Authenticate if credentials provided
        if self.client_id and self.client_secret:
            self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with Sentinel Hub OAuth2."""
        auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        try:
            response: Response = requests.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=10,
            )
            if response.status_code == 200:
                self.access_token: Any = response.json().get("access_token")
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Authentication error: {e}")
            return False

    def get_collection(self, collection_id: str) -> dict | None:
        """Fetch BYOC collection metadata from Sentinel Hub Catalog API."""
        # BYOC collections require the 'byoc-' prefix in the API
        byoc_id = f"byoc-{collection_id}"
        url = f"{self.base_url}/catalog/v1/collections/{byoc_id}"

        headers: dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response: Response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 503:
                logger.warning(
                    f"Sentinel Hub API temporarily unavailable (503) for {byoc_id}"
                )
                return None
            else:
                logger.warning(f"API error {response.status_code} for {byoc_id}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error querying Catalog API for {byoc_id}: {e}")
            return None

    def fetch_collections(self, collection_ids: set[str]) -> dict[str, dict]:
        """Fetch metadata for all collection IDs."""
        logger.info(
            f"Querying Sentinel Hub Catalog API for {len(collection_ids)} collections"
        )

        available = 0
        unavailable = 0

        for coll_id in sorted(collection_ids):
            data = self.get_collection(coll_id)
            if data:
                self.collections[coll_id] = data
                available += 1
            else:
                unavailable += 1

        logger.info(f"Available in CDSE: {available}")
        logger.info(f"Not found in CDSE: {unavailable}")

        return self.collections
