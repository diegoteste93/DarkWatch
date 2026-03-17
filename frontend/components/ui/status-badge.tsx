import clsx from 'clsx';

const palette: Record<string, string> = {
  running: 'bg-accent/20 text-accent',
  completed: 'bg-success/20 text-success',
  partial_failed: 'bg-warning/20 text-warning',
  failed: 'bg-critical/20 text-critical',
  pending: 'bg-slate-700 text-slate-200',
  new: 'bg-cyan/20 text-cyan',
  seen: 'bg-slate-700 text-slate-200',
  resolved: 'bg-success/20 text-success'
};

export function StatusBadge({ value }: { value: string }) {
  return <span className={clsx('px-2 py-1 text-xs rounded-full', palette[value] ?? 'bg-slate-700')}>{value}</span>;
}
