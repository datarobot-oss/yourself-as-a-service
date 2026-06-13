import { useState, useEffect } from 'react';
import cronstrue from 'cronstrue';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useCreateScheduledJob, useUpdateScheduledJob } from '@/api/schedule';
import type { ScheduledJobUI } from '@/api/schedule';
import { isAxiosError } from 'axios';

interface ScheduleJobFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  job?: ScheduledJobUI;
}

const CRON_EXAMPLES: { label: string; value: string }[] = [
  { label: 'Every day 9am', value: '0 9 * * *' },
  { label: 'Weekdays 9am', value: '0 9 * * 1-5' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every Monday', value: '0 9 * * 1' },
];

function getCronDescription(cron: string): { description: string; isValid: boolean } {
  if (!cron.trim()) return { description: '', isValid: true };
  try {
    return { description: cronstrue.toString(cron), isValid: true };
  } catch {
    return { description: 'Invalid cron expression', isValid: false };
  }
}

export const ScheduleJobForm = ({ open, onOpenChange, job }: ScheduleJobFormProps) => {
  const isEdit = !!job;

  const [name, setName] = useState('');
  const [cron, setCron] = useState('');
  const [prompt, setPrompt] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [cronError, setCronError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(job?.name ?? '');
    setCron(job?.cron ?? '');
    setPrompt(job?.prompt ?? '');
    setEnabled(job?.enabled ?? true);
    setCronError(null);
  }, [open, job]);

  const createMutation = useCreateScheduledJob();
  const updateMutation = useUpdateScheduledJob();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const cronInfo = getCronDescription(cron);

  const handleSubmit = async () => {
    setCronError(null);
    try {
      if (isEdit) {
        await updateMutation.mutateAsync({ id: job.id, name, cron, prompt, enabled });
      } else {
        await createMutation.mutateAsync({ name, cron, prompt, enabled });
      }
      onOpenChange(false);
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 422) {
        setCronError(err.response.data?.detail ?? 'Invalid cron expression');
        return;
      }
      throw err;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[540px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Scheduled Job' : 'New Scheduled Job'}</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Daily standup recap"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">Cron schedule</label>
            <Input
              value={cron}
              onChange={e => setCron(e.target.value)}
              placeholder="0 9 * * 1-5"
              className={cronError ? 'border-destructive' : ''}
            />
            <div className="flex flex-wrap gap-1.5">
              {CRON_EXAMPLES.map(ex => (
                <button
                  key={ex.value}
                  type="button"
                  onClick={() => setCron(ex.value)}
                  className="rounded border px-2 py-0.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors font-mono"
                >
                  {ex.value}
                  <span className="ml-1 font-sans not-italic text-muted-foreground/70">
                    — {ex.label}
                  </span>
                </button>
              ))}
            </div>
            {cronError ? (
              <p className="text-sm text-destructive">{cronError}</p>
            ) : (
              <p
                className={`text-sm ${cronInfo.isValid ? 'text-muted-foreground' : 'text-destructive'}`}
              >
                {cronInfo.description}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">Prompt</label>
            <Textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Summarize today's activity and post to Slack…"
              rows={6}
            />
          </div>

          <div className="flex items-center gap-3">
            <Switch checked={enabled} onCheckedChange={setEnabled} id="schedule-enabled" />
            <label htmlFor="schedule-enabled" className="text-sm font-medium cursor-pointer">
              Enabled
            </label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isPending || !name.trim() || !cron.trim() || !prompt.trim()}
          >
            {isEdit ? 'Save changes' : 'Create job'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
