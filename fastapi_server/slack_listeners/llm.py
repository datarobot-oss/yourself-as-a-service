import json
import logging
import re
import textwrap
from typing import Any

from litellm import completion
from slack_bolt import App, Say

from app.config import Config
from app.slack_utils import split_message
from slack_app import OWNER_USER_ID

config = Config()

log = logging.getLogger(__name__)


def get_my_id(client: Any) -> str:
    return client.auth_test().data["user_id"]  # type: ignore[no-any-return]


def post_with_pagination(
    say: Say,
    text: str,
    thread_ts: str | None = None,
    channel: str | None = None,
) -> None:
    """Post a message, splitting into multiple messages if needed."""
    if not text or not text.strip():
        text = "Error: Empty message content"

    chunks = split_message(text)

    # Post the first chunk
    result = say(
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunks[0]}}],
        thread_ts=thread_ts,
        channel=channel,
    )

    # If there are more chunks, post them as threaded replies
    if len(chunks) > 1:
        first_msg_ts = thread_ts or result["ts"]
        for chunk in chunks[1:]:
            say(
                blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": chunk}}],
                thread_ts=first_msg_ts,
                channel=channel,
            )


def ask_caas(message: str, bot_user_id: str, requester_user_id: str) -> str:
    message = message.replace("Store this:", "")
    response = completion(
        model="unknown",
        messages=[
            {
                "role": "user",
                "content": textwrap.dedent(f"""
                You are {bot_user_id} and they are {requester_user_id}
                Please respond in Slack flavored markdown to the following prompt: {message}
                """),
            }
        ],
        api_base=config.agent_endpoint,
        api_key=config.datarobot_api_token,
        custom_llm_provider="openai",
    )

    content = response.choices[0].message.content
    if content:
        return str(content)

    return "Error: Received empty response from LLM"


def get_thread_context(
    client: Any, channel: str, thread_ts: str, fallback_text: str
) -> str:
    """Fetch up to 20 messages from a thread."""
    try:
        res = client.conversations_replies(channel=channel, ts=thread_ts, limit=20)
        messages = res.data.get("messages", [])
        return "\n".join(
            [f"<@{m.get('user', 'unknown')}>: {m.get('text', '')}" for m in messages]
        )
    except Exception:
        return fallback_text


def evaluate_mention(
    client: Any,
    channel: str,
    message_ts: str,
    context: str,
    my_user: str,
    their_user: str,
    target_user_id: str,
) -> None:
    """Evaluate the mention and optionally DM the target user."""
    context = context.replace("Store this:", "")
    prompt_data = {
        "task_type": "mention_evaluation",
        "content": context,
    }

    payload = json.dumps(prompt_data)
    log.info(
        "evaluate_mention: sending payload=%r to agent_endpoint=%r",
        payload,
        config.agent_endpoint,
    )
    response = completion(
        model="unknown",
        messages=[{"role": "user", "content": payload}],
        api_base=config.agent_endpoint,
        api_key=config.datarobot_api_token,
        custom_llm_provider="openai",
    )
    response_text = str(response.choices[0].message.content or "")
    log.info("evaluate_mention: raw response_text=%r", response_text)

    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text.strip())

    try:
        evaluation = json.loads(stripped)
        notify = evaluation.get("notify_user", False)
        category = evaluation.get("category", "unknown")
        eval_message = evaluation.get("message", response_text)
        log.info("evaluate_mention: parsed OK notify=%r category=%r", notify, category)
    except json.JSONDecodeError as e:
        log.warning(
            "evaluate_mention: json.JSONDecodeError parsing response: %s — raw: %r",
            e,
            response_text,
        )
        notify = True
        category = "parse_error"
        eval_message = response_text

    if not notify:
        return

    try:
        permalink_res = client.chat_getPermalink(channel=channel, message_ts=message_ts)
        permalink = permalink_res.data.get("permalink", "")
    except Exception:
        permalink = ""

    link_text = f" (<{permalink}|Jump to message>)" if permalink else ""
    dm_text = f"*[{category}]* You were mentioned in <#{channel}>{link_text}.\n\n{eval_message}"
    try:
        client.chat_postMessage(
            channel=target_user_id,
            text=dm_text,
        )
    except Exception as e:
        logging.getLogger(__name__).error(f"Error sending DM to evaluate mention: {e}")


def register_app(app: App) -> None:
    """Modularize app handlers into multiple files."""

    @app.event("message")
    def handle_message(event: Any, client: Any, say: Say) -> None:
        """Handle messages in DMs, and monitor channels for user mentions."""
        log.debug("handle_message event received: %s", event)

        if event.get("subtype") is not None:
            log.debug("Ignoring message with subtype: %s", event.get("subtype"))
            return

        channel_type = event.get("channel_type")
        message_text = event.get("text", "")
        their_user = event.get("user")

        log.info(
            "handle_message: channel_type=%r user=%r text=%r",
            channel_type,
            their_user,
            message_text,
        )

        my_user = get_my_id(client)

        if channel_type == "im":
            log.info("Handling DM from %s", their_user)
            channel = event.get("channel")
            ts = event.get("ts")
            client.reactions_add(channel=channel, timestamp=ts, name="thinking_face")
            try:
                response = ask_caas(
                    message=message_text,
                    bot_user_id=my_user,
                    requester_user_id=their_user,
                )
            finally:
                client.reactions_remove(
                    channel=channel, timestamp=ts, name="thinking_face"
                )
            post_with_pagination(say=say, text=response)
            return

        owner_mention = f"<@{OWNER_USER_ID}>"
        is_channel_message = (
            channel_type in ("channel", "group", "mpim") or not channel_type
        )
        is_owner_mentioned = owner_mention in message_text
        log.info(
            "Channel message check: is_channel_message=%r is_owner_mentioned=%r (looking for %r)",
            is_channel_message,
            is_owner_mentioned,
            owner_mention,
        )

        if is_channel_message and is_owner_mentioned:
            thread_ts = event.get("thread_ts") or event.get("ts")
            channel = event.get("channel")
            fallback = f"<@{their_user}>: {message_text}"

            context = get_thread_context(client, channel, thread_ts, fallback)
            log.info(
                "Evaluating mention in channel=%s thread_ts=%s", channel, thread_ts
            )
            evaluate_mention(
                client=client,
                channel=channel,
                message_ts=event.get("ts"),
                context=context,
                my_user=my_user,
                their_user=their_user,
                target_user_id=OWNER_USER_ID,
            )

    @app.event("app_mention")
    def mention(event: Any, client: Any, say: Say) -> None:
        """Handle direct mentions."""
        message_text = event["text"]
        my_user = get_my_id(client)
        their_user = event["user"]
        channel = event["channel"]
        ts = event["ts"]

        client.reactions_add(channel=channel, timestamp=ts, name="thinking_face")
        try:
            response = ask_caas(
                message=message_text,
                bot_user_id=my_user,
                requester_user_id=their_user,
            )
        finally:
            client.reactions_remove(channel=channel, timestamp=ts, name="thinking_face")

        post_with_pagination(say=say, text=response, thread_ts=ts)

    @app.event("reaction_added")
    def react(event: Any, client: Any, say: Say) -> None:
        """Handle folks adding a :caas: emoji."""
        if (
            event["reaction"] != "caas"
            or event["item"]["type"] != "message"
            or event["item_user"] is None
        ):
            return

        channel = event["item"]["channel"]
        res = client.conversations_history(
            channel=channel,
            latest=event["item"]["ts"],
            limit=1,
            inclusive=True,
        )
        message_text = res.data["messages"][0]["text"]
        ts = res.data["messages"][0]["ts"]
        my_user = get_my_id(client)
        their_user = event["item_user"]

        client.reactions_add(channel=channel, timestamp=ts, name="thinking_face")
        try:
            response = ask_caas(
                message=message_text,
                bot_user_id=my_user,
                requester_user_id=their_user,
            )
        finally:
            client.reactions_remove(channel=channel, timestamp=ts, name="thinking_face")
        post_with_pagination(
            say=say,
            text=response,
            thread_ts=ts,
            channel=channel,
        )

    @app.command("/ask_CaaS")
    def repeat_text(ack: Any, client: Any, respond: Any, command: Any) -> None:
        ack()
        message_text = command["text"]
        my_user = get_my_id(client)
        their_user = command["user"]

        response = ask_caas(
            message=message_text,
            bot_user_id=my_user,
            requester_user_id=their_user,
        )

        chunks = split_message(response)

        respond(chunks[0])

        if len(chunks) > 1:
            for chunk in chunks[1:]:
                client.chat_postMessage(
                    channel=command["channel_id"],
                    text=chunk,
                )
