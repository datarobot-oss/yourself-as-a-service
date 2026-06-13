import { useState } from 'react';
import { Link } from 'react-router-dom';
import cronstrue from 'cronstrue';
import { Pencil, Trash2, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ScheduleJobForm } from '@/components/ScheduleJobForm';
import { ScheduleDeleteDialog } from '@/components/ScheduleDeleteDialog';
import {
  useFetchScheduledJobs,
  useUpdateScheduledJob,
  useDeleteScheduledJob,
} from '@/api/schedule';
import type { ScheduledJobUI } from '@/api/schedule';
import { PATHS } from '@/constants/path';

const PROMPT_MAX_CHARS = 80;

function truncatePrompt(prompt: string): string {
  return prompt.length > PROMPT_MAX_CHARS ? `${prompt.slice(0, PROMPT_MAX_CHARS)}…` : prompt;
}

function safeCronDescription(cron: string): string {
  try {
    return cronstrue.toString(cron);
  } catch {
    return '';
  }
}

export const SchedulePage = () => {
  const { data: jobs, isLoading } = useFetchScheduledJobs();
  const updateMutation = useUpdateScheduledJob();
  const deleteMutation = useDeleteScheduledJob();

  const [formOpen, setFormOpen] = useState(false);
  const [editJob, setEditJob] = useState<ScheduledJobUI | undefined>(undefined);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteJob, setDeleteJob] = useState<ScheduledJobUI | null>(null);

  const handleNewJob = () => {
    setEditJob(undefined);
    setFormOpen(true);
  };

  const handleEditJob = (job: ScheduledJobUI) => {
    setEditJob(job);
    setFormOpen(true);
  };

  const handleDeleteJob = (job: ScheduledJobUI) => {
    setDeleteJob(job);
    setDeleteOpen(true);
  };

  const handleToggleEnabled = (job: ScheduledJobUI, enabled: boolean) => {
    updateMutation.mutate({ id: job.id, enabled });
  };

  const handleConfirmDelete = () => {
    if (!deleteJob) return;
    deleteMutation.mutate({ id: deleteJob.id });
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-5xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to={PATHS.CHAT_EMPTY} className="gap-2 px-3 py-2">
            <X />
          </Link>
          <h1 className="text-2xl font-semibold">Scheduled Jobs</h1>
        </div>
        <Button onClick={handleNewJob}>
          <Plus className="size-4 mr-2" />
          New Job
        </Button>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!isLoading && (!jobs || jobs.length === 0) && (
        <div className="flex flex-col items-center justify-center gap-4 py-20 text-center text-muted-foreground">
          <p>No scheduled jobs yet. Create one to run prompts on a schedule.</p>
          <Button onClick={handleNewJob}>
            <Plus className="size-4 mr-2" />
            New Job
          </Button>
        </div>
      )}

      {!isLoading && jobs && jobs.length > 0 && (
        <div className="rounded-md border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50 text-muted-foreground">
                <th className="py-3 px-4 text-left font-medium">Name</th>
                <th className="py-3 px-4 text-left font-medium">Cron</th>
                <th className="py-3 px-4 text-left font-medium">Prompt</th>
                <th className="py-3 px-4 text-left font-medium">Enabled</th>
                <th className="py-3 px-4 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => {
                const cronDescription = safeCronDescription(job.cron);
                return (
                  <tr key={job.id} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="py-3 px-4 font-medium">{job.name}</td>
                    <td className="py-3 px-4">
                      <span className="font-mono">{job.cron}</span>
                      {cronDescription && (
                        <p className="text-xs text-muted-foreground mt-0.5">{cronDescription}</p>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="cursor-default">{truncatePrompt(job.prompt)}</span>
                        </TooltipTrigger>
                        {job.prompt.length > PROMPT_MAX_CHARS && (
                          <TooltipContent className="max-w-sm whitespace-pre-wrap">
                            {job.prompt}
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </td>
                    <td className="py-3 px-4">
                      <Switch
                        checked={job.enabled}
                        onCheckedChange={checked => handleToggleEnabled(job, checked)}
                      />
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEditJob(job)}
                          aria-label={`Edit ${job.name}`}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteJob(job)}
                          aria-label={`Delete ${job.name}`}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <ScheduleJobForm
        open={formOpen}
        onOpenChange={open => {
          setFormOpen(open);
          if (!open) setEditJob(undefined);
        }}
        job={editJob}
      />

      {deleteJob && (
        <ScheduleDeleteDialog
          open={deleteOpen}
          setOpen={setDeleteOpen}
          job={deleteJob}
          onConfirm={handleConfirmDelete}
        />
      )}
    </div>
  );
};
