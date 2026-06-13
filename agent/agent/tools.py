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

    Only call this tool when the user explicitly says
    'Store this to my knowledge base:' and includes content to store.

    Args:
        content: The text content to store.
        file_name: A short descriptive name for the file (without extension or date).
            A date suffix and .txt extension will be appended automatically.

    Returns:
        A confirmation message with the stored file name.
    """
    dated_name = f"{file_name}_{date.today().strftime('%Y%m%d')}.txt"
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
