'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '@/components/layout/app-shell';
import { DataTable } from '@/components/tables/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import { toastError } from '@/hooks/use-toast';

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/dashboard/findings', label: 'Findings' },
  { href: '/dashboard/targets', label: 'Targets' },
  { href: '/dashboard/runs', label: 'Runs' },
  { href: '/dashboard/settings', label: 'Settings' }
];

export default function RunsPage() {
  const { me } = useAuthStore();
  const tenantId = me?.tenant_id;
  const qc = useQueryClient();

  const { data } = useQuery({ queryKey: ['runs', tenantId], enabled: !!tenantId, queryFn: async () => (await api.get(`/tenants/${tenantId}/runs?page=1&page_size=50`)).data });

  const scan = useMutation({
    mutationFn: async () => api.post(`/tenants/${tenantId}/scan`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['runs', tenantId] }),
    onError: (err: any) => toastError(err?.detail ?? 'Erro ao executar scan')
  });

  return (
    <AppShell title="Runs" items={items}>
      <button onClick={() => scan.mutate()} className="rounded-lg bg-accent px-4 py-2">Run Scan</button>
      <DataTable headers={['Run ID', 'Status', 'Started', 'Finished', 'New Findings']}>
        {data?.items?.map((r: any) => (
          <tr key={r.id} className="border-t border-slate-800">
            <td className="p-3">{r.id}</td>
            <td className="p-3"><StatusBadge value={r.status} /></td>
            <td className="p-3">{new Date(r.started_at).toLocaleString()}</td>
            <td className="p-3">{r.finished_at ? new Date(r.finished_at).toLocaleString() : '-'}</td>
            <td className="p-3">{r.new_findings}</td>
          </tr>
        ))}
      </DataTable>
    </AppShell>
  );
}
