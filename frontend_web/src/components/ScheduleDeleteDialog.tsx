import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { ScheduledJobUI } from '@/api/schedule';

interface ScheduleDeleteDialogProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  job: ScheduledJobUI;
  onConfirm: () => void;
}

export const ScheduleDeleteDialog = ({
  open,
  setOpen,
  job,
  onConfirm,
}: ScheduleDeleteDialogProps) => (
  <Dialog open={open} onOpenChange={setOpen}>
    <DialogContent className="sm:max-w-[440px]">
      <DialogHeader>
        <DialogTitle>Delete scheduled job?</DialogTitle>
      </DialogHeader>
      <DialogDescription>
        Are you sure you want to delete <strong>«{job.name}»</strong>? This action cannot be undone.
      </DialogDescription>
      <DialogFooter>
        <Button variant="ghost" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        <Button
          variant="destructive"
          onClick={() => {
            onConfirm();
            setOpen(false);
          }}
        >
          Delete
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
