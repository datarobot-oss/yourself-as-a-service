from fastapi import APIRouter, Request
from pydantic import BaseModel

app_config_router = APIRouter(tags=["App Config"])


class AppConfigSchema(BaseModel):
    bot_name: str


@app_config_router.get("/app-config/")
async def get_app_config(request: Request) -> AppConfigSchema:
    """Return public application configuration for the frontend."""
    config = request.app.state.deps.config
    return AppConfigSchema(bot_name=config.bot_name)
