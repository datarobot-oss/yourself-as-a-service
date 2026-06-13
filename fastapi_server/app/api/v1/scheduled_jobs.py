import logging
import uuid as uuidpkg

from apscheduler.triggers.cron import CronTrigger
from datarobot.auth.session import AuthCtx
from datarobot.auth.typing import Metadata
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.ctx import must_get_auth_ctx
from app.schedules import (
    ScheduledJob,
    ScheduledJobCreate,
    ScheduledJobRepository,
    ScheduledJobUpdate,
)
from app.schedules.service import SchedulerService
from app.users.user import User, UserRepository

log = logging.getLogger(__name__)
schedule_router = APIRouter(prefix="/schedule", tags=["Schedule"])


def _validate_cron(cron: str) -> None:
    try:
        CronTrigger.from_crontab(cron)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid cron expression: {e}",
        ) from e


async def _get_current_user(user_repo: UserRepository, user_id: int) -> User:
    user = await user_repo.get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@schedule_router.get("")
async def list_scheduled_jobs(
    request: Request,
    auth_ctx: AuthCtx[Metadata] = Depends(must_get_auth_ctx),
) -> list[ScheduledJob]:
    user: User = await _get_current_user(
        request.app.state.deps.user_repo, int(auth_ctx.user.id)
    )
    repo: ScheduledJobRepository = request.app.state.deps.schedule_repo
    return list(await repo.list_for_user(user.uuid))


@schedule_router.post("", status_code=status.HTTP_201_CREATED)
async def create_scheduled_job(
    request: Request,
    data: ScheduledJobCreate,
    auth_ctx: AuthCtx[Metadata] = Depends(must_get_auth_ctx),
) -> ScheduledJob:
    _validate_cron(data.cron)

    user: User = await _get_current_user(
        request.app.state.deps.user_repo, int(auth_ctx.user.id)
    )
    repo: ScheduledJobRepository = request.app.state.deps.schedule_repo
    scheduler: SchedulerService = request.app.state.deps.scheduler

    job = await repo.create(data, user.uuid)
    scheduler.add_job(job)
    return job


@schedule_router.patch("/{job_id}")
async def update_scheduled_job(
    request: Request,
    job_id: uuidpkg.UUID,
    data: ScheduledJobUpdate,
    auth_ctx: AuthCtx[Metadata] = Depends(must_get_auth_ctx),
) -> ScheduledJob:
    if data.cron is not None:
        _validate_cron(data.cron)

    user: User = await _get_current_user(
        request.app.state.deps.user_repo, int(auth_ctx.user.id)
    )
    repo: ScheduledJobRepository = request.app.state.deps.schedule_repo
    scheduler: SchedulerService = request.app.state.deps.scheduler

    job = await repo.update(job_id, user.uuid, data)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled job not found"
        )

    scheduler.update_job(job)
    return job


@schedule_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_job(
    request: Request,
    job_id: uuidpkg.UUID,
    auth_ctx: AuthCtx[Metadata] = Depends(must_get_auth_ctx),
) -> None:
    user: User = await _get_current_user(
        request.app.state.deps.user_repo, int(auth_ctx.user.id)
    )
    repo: ScheduledJobRepository = request.app.state.deps.schedule_repo
    scheduler: SchedulerService = request.app.state.deps.scheduler

    deleted = await repo.delete(job_id, user.uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled job not found"
        )

    scheduler.remove_job(job_id)
