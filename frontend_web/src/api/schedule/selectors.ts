import { ScheduledJob, ScheduledJobUI } from './types';

export function selectScheduledJobs(res: { data: ScheduledJob[] }): ScheduledJobUI[] {
  return res.data.map(job => ({
    id: job.id,
    name: job.name,
    cron: job.cron,
    prompt: job.prompt,
    enabled: job.enabled,
    createdAt: new Date(job.created_at),
  }));
}
