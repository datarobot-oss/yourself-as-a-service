import json
import logging

from litellm import acompletion
from slack_sdk.web.async_client import AsyncWebClient

from app.config import Config
from app.slack_utils import post_paginated

log = logging.getLogger(__name__)


async def execute_scheduled_job(prompt: str) -> None:
    log.info("Scheduled job triggered — prompt: %.80s", prompt)
    config = Config()
    log.info(
        "Scheduled job config — agent_endpoint=%s slack_bot_token_set=%s slack_owner_user_id=%s",
        config.agent_endpoint or "<not set>",
        bool(config.slack_bot_token),
        config.slack_owner_user_id or "<not set>",
    )

    if not config.agent_endpoint:
        log.warning("Scheduled job skipped: agent_endpoint is not configured")
        return

    if not config.slack_bot_token:
        log.warning("Scheduled job skipped: slack_bot_token is not configured")
        return

    if not config.slack_owner_user_id:
        log.warning("Scheduled job skipped: slack_owner_user_id is not configured")
        return

    payload = json.dumps(
        {
            "task_type": "scheduled_job",
            "content": prompt,
        }
    )
    response = await acompletion(
        model="unknown",
        messages=[{"role": "user", "content": payload}],
        api_base=config.agent_endpoint,
        api_key=config.datarobot_api_token,
        custom_llm_provider="openai",
    )

    content = (
        response.choices[0].message.content
        or "Error: Received empty response from agent"
    )

    client = AsyncWebClient(token=config.slack_bot_token)
    await post_paginated(client, config.slack_owner_user_id, content)
    log.info("Scheduled job delivered response to Slack for prompt: %.80s", prompt)
