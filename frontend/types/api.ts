export type ApiEnvelope<T> = { data: T; message: string };
export type ApiError = { detail: string; code: string; status: number };

export type UserMe = { id: number; email: string; role: 'ADMIN' | 'CLIENT' | string; tenant_id: number | null };
export type DashboardOverview = {
  total_findings: number;
  new_last_24h: number;
  total_targets: number;
  last_run_status: string | null;
  failed_runs: number;
};

export type Target = { id: number; tenant_id: number; type: 'domain' | 'email' | 'keyword'; value: string; active: boolean };
export type Finding = {
  id: number;
  source: string | null;
  email: string | null;
  username: string | null;
  leak_date: string | null;
  url: string | null;
  first_seen: string;
  last_seen: string;
};
export type Run = {
  id: number;
  tenant_id: number;
  status: 'pending' | 'running' | 'completed' | 'partial_failed' | 'failed' | string;
  trigger_type: string;
  started_at: string;
  finished_at: string | null;
  new_findings: number;
  updated_findings: number;
};
