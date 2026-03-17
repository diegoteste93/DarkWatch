'use client';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AppShell } from '@/components/layout/app-shell';
import { DataTable } from '@/components/tables/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/dashboard/findings', label: 'Findings' },
  { href: '/dashboard/targets', label: 'Targets' },
  { href: '/dashboard/runs', label: 'Runs' },
  { href: '/dashboard/settings', label: 'Settings' }
];

export default function FindingsPage() {
  const { me } = useAuthStore();
  const [q, setQ] = useState('');
  const tenantId = me?.tenant_id;
  const queryString = useMemo(() => `page=1&page_size=50&q=${encodeURIComponent(q)}`, [q]);

  const { data } = useQuery({
    queryKey: ['findings', tenantId, q],
    enabled: !!tenantId,
    queryFn: async () => (await api.get(`/tenants/${tenantId}/findings?${queryString}`)).data
  });

  return (
    <AppShell title="Findings" items={items}>
      <input className="rounded-lg bg-slate-900 border border-slate-700 p-2 w-full md:w-80" placeholder="Buscar source/email/username" value={q} onChange={(e) => setQ(e.target.value)} />
      <DataTable headers={['Source', 'Email', 'Username', 'Leak Date', 'Status', 'Severity']}>
        {data?.items?.map((f: any) => (
          <tr key={f.id} className="border-t border-slate-800">
            <td className="p-3">{f.source ?? '-'}</td>
            <td className="p-3">{f.email ?? '-'}</td>
            <td className="p-3">{f.username ?? '-'}</td>
            <td className="p-3">{f.leak_date ?? '-'}</td>
            <td className="p-3"><StatusBadge value="new" /></td>
            <td className="p-3"><StatusBadge value={(f.source || '').includes('critical') ? 'failed' : 'running'} /></td>
          </tr>
        ))}
      </DataTable>
    </AppShell>
  );
}
