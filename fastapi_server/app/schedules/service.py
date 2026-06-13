import logging
import uuid as uuidpkg

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.schedules import ScheduledJob, ScheduledJobRepository
from app.schedules.worker import execute_scheduled_job

log = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.start()
        log.info("Scheduler started (timezone=%s)", self._scheduler.timezone)

    async def load_jobs(self, schedule_repo: ScheduledJobRepository) -> None:
        jobs = await schedule_repo.list_all()
        for job in jobs:
            if job.enabled:
                self._add_job(job)
        log.info(
            "Loaded %d scheduled job(s) from DB",
            sum(1 for j in jobs if j.enabled),
        )

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        log.info("Scheduler shut down")

    def _add_job(self, job: ScheduledJob) -> None:
        trigger = CronTrigger.from_crontab(job.cron)
        self._scheduler.add_job(
            execute_scheduled_job,
            trigger,
            id=str(job.id),
            kwargs={"prompt": job.prompt},
            replace_existing=True,
        )
        log.info(
            "Scheduled job added: %s (%s) [%s] (scheduler tz=%s)",
            job.name,
            job.cron,
            job.id,
            self._scheduler.timezone,
        )

    def add_job(self, job: ScheduledJob) -> None:
        if not job.enabled:
            return
        self._add_job(job)

    def remove_job(self, job_id: uuidpkg.UUID) -> None:
        try:
            self._scheduler.remove_job(str(job_id))
            log.info("Scheduled job removed: %s", job_id)
        except JobLookupError:
            pass

    def update_job(self, job: ScheduledJob) -> None:
        self.remove_job(job.id)
        self.add_job(job)
