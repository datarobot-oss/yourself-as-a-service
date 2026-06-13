"""Pull all knowledge base files from DataRobot into ../knowledgebase/."""

import logging
import sys
from pathlib import Path

import datarobot as dr
from datarobot.models.files import FilesCatalogSearch

from agent.tools import KNOWLEDGE_BASE_TAG

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

KNOWLEDGEBASE_DIR = Path(__file__).parent.parent / "knowledgebase"


def main() -> int:
    dr.Client()

    KNOWLEDGEBASE_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items: list[FilesCatalogSearch] = dr.models.Files.search_catalog(
        tags=[KNOWLEDGE_BASE_TAG],
        limit=0,
    )

    if not catalog_items:
        log.info("No knowledge base items found with tag '%s'.", KNOWLEDGE_BASE_TAG)
        return 0

    log.info(
        "Found %d catalog item(s). Syncing to %s",
        len(catalog_items),
        KNOWLEDGEBASE_DIR,
    )

    for item in catalog_items:
        files_container = dr.models.Files.get(item.id)
        contained = files_container.list_contained_files(limit=0)
        for f in contained:
            dest = KNOWLEDGEBASE_DIR / f.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            files_container.download(file_name=f.name, file_path=str(dest))
            log.info("  downloaded: %s (%d bytes)", f.name, f.size)

    log.info("Sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
