"""Main script for counting CLMS collections available in CDSE."""

import argparse
import csv
import logging
import sys
from datetime import datetime
from typing import Any, Literal, TextIO

from dotenv import load_dotenv

from src.id_extractor import CollectionIDExtractor
from src.sh_catalog import SentinelHubCatalog


def save_collections_to_csv(
    all_ids: set[str], available_collections: dict[str, dict], output_file: str
) -> None:
    """Save collections to CSV file with minimal information.

    Args:
        all_ids: All collection IDs found in documentation
        available_collections: Dictionary of available collections from API
        output_file: Path to save CSV file
    """
    logger: logging.Logger = logging.getLogger(__name__)

    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["BYOC ID", "Name", "Available", "Last Checked"])

            # Write available collections
            for coll_id in sorted(available_collections.keys()):
                data = available_collections[coll_id]
                byoc_id = f"byoc-{coll_id}"
                name = data.get("title", "Unknown")
                writer.writerow([byoc_id, name, True, datetime.now().isoformat()])

            # Write unavailable collections
            unavailable_ids: set[str] = all_ids - set(available_collections.keys())
            for coll_id in sorted(unavailable_ids):
                byoc_id = f"byoc-{coll_id}"
                writer.writerow(
                    [
                        byoc_id,
                        "Unknown",
                        False,
                        datetime.now().isoformat(),
                    ]
                )

        logger.info(f"Collections saved to {output_file}")
        print(f"✓ Collections saved to {output_file}")
    except OSError as e:
        logger.error(f"Failed to save CSV: {e}")
        print(f"✗ Failed to save CSV: {e}")


def setup_logging(log_level: str | None) -> None:
    """Configure logging with appropriate level.

    Args:
        log_level: Logging level ('info' or 'debug'). None disables all logging.
    """
    root_logger: logging.Logger = logging.getLogger()

    if log_level:
        handler: logging.StreamHandler[TextIO | Any] = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)

        level: Literal[10, 20] = (
            logging.DEBUG if log_level.lower() == "debug" else logging.INFO
        )
        root_logger.setLevel(level)
        root_logger.addHandler(handler)
    else:
        # Disable all logging when no log level specified
        root_logger.setLevel(logging.CRITICAL + 1)


def main(log_level: str | None = None) -> None:
    """
    Count CLMS collections available in CDSE.

    Args:
        log_level: Logging level ('info', 'debug', or None for silent)
    """
    setup_logging(log_level)
    logger: logging.Logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("CLMS Collections Status Tool")
    logger.info("=" * 60)

    # 1. Extract IDs from documentation
    extractor = CollectionIDExtractor(
        repo_owner="eu-cdse",
        repo_name="documentation",
        branch="publish",
        target_path="APIs/SentinelHub/Data/clms",
    )
    collection_ids: set[str] = extractor.extract_all_ids()

    logger.info("")
    logger.info(
        f"Found {len(collection_ids)} unique collection IDs in the documentation."
    )

    # 2. Query Sentinel Hub Catalog API
    catalog = SentinelHubCatalog()
    collections = catalog.fetch_collections(collection_ids)

    available_count: int = len(collections)
    unavailable_ids: set[str] = collection_ids - set(collections.keys())

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Available collections in CDSE: {available_count}")
    logger.info(f"Unavailable collection IDs: {len(unavailable_ids)}")
    logger.info("=" * 60)

    if log_level == "debug" and unavailable_ids:
        logger.debug(f"Unavailable IDs: {sorted(unavailable_ids)}")

    # 3. Save collections to CSV
    output_file = "CLMS_SH_collection_status.csv"
    save_collections_to_csv(
        all_ids=collection_ids,
        available_collections=collections,
        output_file=output_file,
    )


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    parser = argparse.ArgumentParser(
        description="Count CLMS collections available in CDSE"
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["info", "debug"],
        help="Logging level (info or debug). Omit for silent mode.",
    )
    args: argparse.Namespace = parser.parse_args()

    main(log_level=args.log_level)
