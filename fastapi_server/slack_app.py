import logging
import signal
import sys
from typing import Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import slack_listeners as listeners
from app.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

config = Config()

OWNER_USER_ID = config.slack_owner_user_id or ""
BOT_NAME = config.bot_name or "YaaS"

BOT_TOKEN = config.slack_bot_token
APP_TOKEN = config.slack_app_token

app_handler: SocketModeHandler | None = None


def registration(app: App) -> None:
    """Iterate through all base modules and register them with App."""
    for base_module in (listeners,):
        for module_name in base_module.__all__:
            module = getattr(base_module, module_name)
            if hasattr(module, "register_app"):
                module.register_app(app)


def initiate_app_handler() -> None:
    global app_handler
    app = App(token=BOT_TOKEN)
    registration(app)
    app_handler = SocketModeHandler(app, APP_TOKEN)


def handle_shutdown(signum: int, frame: Any) -> None:
    assert app_handler is not None
    app_handler.close()  # type: ignore[no-untyped-call]
    sys.exit(0)


if __name__ == "__main__":
    if BOT_TOKEN and APP_TOKEN:
        initiate_app_handler()

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

        assert app_handler is not None
        app_handler.start()  # type: ignore[no-untyped-call]
    else:
        sys.exit(0)
