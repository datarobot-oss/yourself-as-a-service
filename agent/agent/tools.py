import io
import logging
from datetime import date

import datarobot as dr
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from agent.config import Config

log = logging.getLogger(__name__)

KNOWLEDGE_BASE_TAG = "yaas_knowledge_base"


def make_tavily_search_tool() -> TavilySearchResults:
    config = Config()
    return TavilySearchResults(
        max_results=3,
        search_depth="basic",
        tavily_api_key=config.tavily_api_key,
    )


@tool
def store_to_knowledge_base(content: str, file_name: str) -> str:
    """Store text content into the DataRobot knowledge base.

    Only call this tool when the user explicitly requests storing content to the knowledge base.

    IMPORTANT SAFETY CONSTRAINTS FOR CALLING THIS TOOL:
    - file_name MUST be a simple filename without path separators ('/', '\\') or relative path tokens ('..').
    - content MUST be under 50,000 characters. If content is larger, do NOT call this tool; ask the user to truncate it.

    Args:
        content: The text content to store.
        file_name: A short descriptive name for the file (without extension or path).

    Returns:
        A confirmation message with the stored file name.
    """
    MAX_CONTENT_LENGTH = 50_000
    if len(content) > MAX_CONTENT_LENGTH:
        return f"Error: Content size ({len(content)} chars) exceeds maximum allowed limit of {MAX_CONTENT_LENGTH} characters."

    import os
    import re

    # Sanitize file_name to prevent path traversal and invalid path characters
    clean_filename = os.path.basename(file_name)
    clean_filename = re.sub(r"[^\w\.-]", "_", clean_filename)
    if not clean_filename or clean_filename in (".", ".."):
        clean_filename = "stored_doc"

    dated_name = f"{clean_filename}_{date.today().strftime('%Y%m%d')}.txt"
    log.info(
        "store_to_knowledge_base: uploading %s (%d bytes)", dated_name, len(content)
    )

    dr.Client()
    buf = io.BytesIO(content.encode())
    buf.name = dated_name
    files_item = dr.models.Files.create_from_file(
        filelike=buf,
        tags=[KNOWLEDGE_BASE_TAG],
        use_archive_contents=False,
    )

    log.info(
        "store_to_knowledge_base: stored %s as catalog item %s",
        dated_name,
        files_item.id,
    )
    return (
        f"Stored to knowledge base as `{dated_name}` (catalog id: `{files_item.id}`)."
    )
