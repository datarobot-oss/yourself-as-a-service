import logging

from slack_sdk.web.async_client import AsyncWebClient

log = logging.getLogger(__name__)

# Slack has a 3000 char limit for mrkdwn text, we use 2900 to be safe
MAX_SLACK_TEXT_LENGTH = 2900


def split_message(text: str, max_length: int = MAX_SLACK_TEXT_LENGTH) -> list[str]:
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_pos = text.rfind("\n\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    return chunks


async def post_paginated(
    client: AsyncWebClient,
    channel: str,
    content: str,
) -> None:
    if not content or not content.strip():
        content = "Error: Empty message content"

    chunks = split_message(content)
    result = await client.chat_postMessage(
        channel=channel,
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunks[0]}}],
    )
    for chunk in chunks[1:]:
        await client.chat_postMessage(
            channel=channel,
            thread_ts=result["ts"],
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunk}}],
        )
