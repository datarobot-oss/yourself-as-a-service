import textwrap
from typing import Any

from slack_bolt import App, Say

from slack_app import BOT_NAME, OWNER_USER_ID


def register_app(app: App) -> None:
    """Modularize app handlers into multiple files."""

    @app.message("Hello CaaS")
    def hi(message: dict[str, Any], say: Say) -> None:
        say(f"Hi there <@{message['user']}>! :wave:")

    @app.event("app_home_opened")
    def update_home_tab(client: Any, event: dict[str, Any], logger: Any) -> None:
        try:
            client.views_publish(
                user_id=event["user"],
                view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Welcome to {BOT_NAME} <@"
                                + event["user"]
                                + ">! :robot_face:*",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": textwrap.dedent(f"""
                              *About {BOT_NAME}*

                              {BOT_NAME} is a bot made by <@{OWNER_USER_ID}> using DataRobot.

                              It uses the agentic starter app template with a Slack bot using Slack Bolt, and it uses an LLM created via the playground and deployed as a custom model to answer questions using a curated knowledge base embedded as a VDB.

                              All feedback and interest are welcome! Under the hood it is "Yourself as a Service" since it can be easily adapted to anyone by changing the knowledge base and LLM responses. :slightly_smiling_face:
                              """),
                            },
                        },
                    ],
                },
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")
