import { useMutation, useQuery } from '@tanstack/react-query';
import {
  getScheduledJobs,
  createScheduledJob,
  updateScheduledJob,
  deleteScheduledJob,
} from './requests';
import { scheduleKeys } from './keys';
import { selectScheduledJobs } from './selectors';
import { ScheduledJobCreate, ScheduledJobUpdate } from './types';
import { queryClient } from '@/api/query-client';

const staleTime = 60 * 1000;

export function useFetchScheduledJobs() {
  return useQuery({
    queryFn: ({ signal }) => getScheduledJobs({ signal }),
    queryKey: scheduleKeys.list,
    select: selectScheduledJobs,
    staleTime,
  });
}

export function useCreateScheduledJob() {
  return useMutation({
    mutationFn: (body: ScheduledJobCreate) => createScheduledJob(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.list });
    },
  });
}

export function useUpdateScheduledJob() {
  return useMutation({
    mutationFn: (vars: ScheduledJobUpdate & { id: string }) => updateScheduledJob(vars),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.list });
    },
  });
}

export function useDeleteScheduledJob() {
  return useMutation({
    mutationFn: ({ id }: { id: string }) => deleteScheduledJob({ id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.list });
    },
  });
}
