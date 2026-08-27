"""Module for extracting BYOC collection IDs from EU-CDSE documentation."""

import logging
import re
from typing import Any

import requests
from requests.models import Response

logger: logging.Logger = logging.getLogger(__name__)


class CollectionIDExtractor:
    """Extract BYOC collection IDs from EU-CDSE documentation."""

    def __init__(self, repo_owner: str, repo_name: str, branch: str, target_path: str):
        self.repo_owner: str = repo_owner
        self.repo_name: str = repo_name
        self.branch: str = branch
        self.target_path: str = target_path
        self.collection_ids: set[str] = set()

        # Pattern to match collection IDs in ```default <ID> ``` blocks
        # IDs are UUIDs: 8-4-4-4-12 format (e.g., 64d015da-e225-48d8-9643-30a453657beb)
        self.id_pattern: re.Pattern[str] = re.compile(
            r"```default\s+([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\s*```",
            re.IGNORECASE | re.MULTILINE,
        )

    def fetch_repository_tree(self) -> list[dict] | None:
        """Fetch entire repository tree in one API call with recursive=1."""
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/git/trees/{self.branch}?recursive=1"
        try:
            response: Response = requests.get(url, timeout=30)
            response.raise_for_status()
            tree_data: Any = response.json()

            if tree_data.get("truncated"):
                logger.warning("Repository tree was truncated by GitHub")

            return tree_data.get("tree", [])
        except requests.RequestException as e:
            logger.error(f"Error fetching repository tree: {e}")
            return None

    def filter_qmd_files(self, tree: list[dict]) -> list[str]:
        """Filter tree for .qmd files in target path."""
        qmd_files = [
            item["path"]
            for item in tree
            if item["path"].startswith(self.target_path)
            and item["path"].endswith(".qmd")
            and item["type"] == "blob"
        ]
        return sorted(qmd_files)

    def fetch_file_content(self, file_path: str) -> str | None:
        """Fetch file from raw.githubusercontent.com (no API rate limit - raw content CDN)."""
        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{file_path}"
        try:
            response: Response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Error fetching {file_path}: {e}")
            return None

    def extract_ids_from_content(self, content: str, file_path: str = "") -> set[str]:
        """Extract collection IDs from ```default <ID> ``` code blocks."""
        ids: set[Any | str] = set()
        matches: list[Any] = self.id_pattern.findall(content)
        for match in matches:
            ids.add(match.lower())

        if ids and file_path:
            logger.info(f"✓ {file_path}")
            for id_val in sorted(ids):
                logger.debug(f"  └─ {id_val}")

        return ids

    def extract_all_ids(self) -> set[str]:
        """Extract all collection IDs from documentation."""
        logger.info("Fetching repository tree...")
        tree = self.fetch_repository_tree()
        if not tree:
            return set()

        logger.info(f"Found {len(tree)} total items in repository")

        qmd_files: list[str] = self.filter_qmd_files(tree)
        logger.info(
            f"Found {len(qmd_files)} .qmd files in {self.repo_owner}/{self.repo_name}/tree/{self.branch}/{self.target_path}"
        )

        logger.info("Extracting collection IDs from .qmd files")
        for file_path in qmd_files:
            content: str | None = self.fetch_file_content(file_path)
            if content:
                ids: set[str] = self.extract_ids_from_content(
                    content, file_path=file_path
                )
                self.collection_ids.update(ids)

        return self.collection_ids
