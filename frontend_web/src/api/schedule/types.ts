export interface ScheduledJob {
  id: string;
  name: string;
  cron: string;
  prompt: string;
  enabled: boolean;
  created_at: string;
}

export interface ScheduledJobUI {
  id: string;
  name: string;
  cron: string;
  prompt: string;
  enabled: boolean;
  createdAt: Date;
}

export interface ScheduledJobCreate {
  name: string;
  cron: string;
  prompt: string;
  enabled?: boolean;
}

export interface ScheduledJobUpdate {
  name?: string;
  cron?: string;
  prompt?: string;
  enabled?: boolean;
}
