import uuid as uuidpkg
from datetime import datetime, timezone
from typing import Sequence, cast

from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel, select

from app.db import DBCtx


class ScheduledJobBase(SQLModel):
    name: str
    cron: str
    prompt: str
    enabled: bool = Field(default=True)


class ScheduledJob(ScheduledJobBase, table=True):
    __tablename__ = "scheduledjob"

    id: uuidpkg.UUID = Field(
        default_factory=uuidpkg.uuid4, primary_key=True, unique=True
    )
    user_uuid: uuidpkg.UUID | None = Field(
        default=None,
        sa_column=Column(
            "user_uuid", ForeignKey("user.uuid", ondelete="CASCADE"), index=True
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ScheduledJobCreate(ScheduledJobBase):
    pass


class ScheduledJobUpdate(SQLModel):
    name: str | None = None
    cron: str | None = None
    prompt: str | None = None
    enabled: bool | None = None


class ScheduledJobRepository:
    def __init__(self, db: DBCtx):
        self._db = db

    async def create(
        self, data: ScheduledJobCreate, user_uuid: uuidpkg.UUID
    ) -> ScheduledJob:
        job = ScheduledJob(**data.model_dump(), user_uuid=user_uuid)
        async with self._db.session(writable=True) as session:
            session.add(job)
            await session.commit()
            await session.refresh(job)
        return job

    async def list_all(self) -> Sequence[ScheduledJob]:
        async with self._db.session() as session:
            result = await session.execute(select(ScheduledJob))
            return result.scalars().all()

    async def list_for_user(self, user_uuid: uuidpkg.UUID) -> Sequence[ScheduledJob]:
        async with self._db.session() as session:
            result = await session.execute(
                select(ScheduledJob).where(ScheduledJob.user_uuid == user_uuid)
            )
            return result.scalars().all()

    async def get_by_id(
        self, job_id: uuidpkg.UUID, user_uuid: uuidpkg.UUID
    ) -> ScheduledJob | None:
        async with self._db.session() as session:
            result = await session.execute(
                select(ScheduledJob).where(
                    ScheduledJob.id == job_id,
                    ScheduledJob.user_uuid == user_uuid,
                )
            )
            return result.scalar_one_or_none()

    async def update(
        self,
        job_id: uuidpkg.UUID,
        user_uuid: uuidpkg.UUID,
        data: ScheduledJobUpdate,
    ) -> ScheduledJob | None:
        async with self._db.session(writable=True) as session:
            result = await session.execute(
                select(ScheduledJob).where(
                    ScheduledJob.id == job_id,
                    ScheduledJob.user_uuid == user_uuid,
                )
            )
            job = result.scalar_one_or_none()
            if job is None:
                return None
            for field, value in data.model_dump(exclude_none=True).items():
                setattr(job, field, value)
            session.add(job)
            await session.commit()
            await session.refresh(job)
        return cast(ScheduledJob, job)

    async def delete(self, job_id: uuidpkg.UUID, user_uuid: uuidpkg.UUID) -> bool:
        async with self._db.session(writable=True) as session:
            result = await session.execute(
                select(ScheduledJob).where(
                    ScheduledJob.id == job_id,
                    ScheduledJob.user_uuid == user_uuid,
                )
            )
            job = result.scalar_one_or_none()
            if job is None:
                return False
            await session.delete(job)
            await session.commit()
        return True
