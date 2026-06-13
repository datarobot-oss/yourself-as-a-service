import { ScheduledJob, ScheduledJobCreate, ScheduledJobUpdate } from './types';
import apiClient from '../apiClient';

export async function getScheduledJobs({ signal }: { signal: AbortSignal }) {
  return apiClient.get<ScheduledJob[]>('v1/schedule', { signal });
}

export async function createScheduledJob(body: ScheduledJobCreate) {
  return apiClient.post<ScheduledJob>('v1/schedule', body);
}

export async function updateScheduledJob({ id, ...body }: ScheduledJobUpdate & { id: string }) {
  return apiClient.patch<ScheduledJob>(`v1/schedule/${id}`, body);
}

export async function deleteScheduledJob({ id }: { id: string }): Promise<void> {
  await apiClient.delete(`v1/schedule/${id}`);
}
