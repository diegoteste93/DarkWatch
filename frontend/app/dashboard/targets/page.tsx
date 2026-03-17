'use client';
import { FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AppShell } from '@/components/layout/app-shell';
import { DataTable } from '@/components/tables/data-table';
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

export default function TargetsPage() {
  const { me } = useAuthStore();
  const tenantId = me?.tenant_id;
  const qc = useQueryClient();
  const [type, setType] = useState('domain');
  const [value, setValue] = useState('');

  const { data } = useQuery({ queryKey: ['targets', tenantId], enabled: !!tenantId, queryFn: async () => (await api.get(`/tenants/${tenantId}/targets?page=1&page_size=50`)).data });

  const mutation = useMutation({
    mutationFn: async () => api.post(`/tenants/${tenantId}/targets`, { type, value, active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['targets', tenantId] });
      setValue('');
    },
    onError: (err: any) => toastError(err?.detail ?? 'Erro ao criar target')
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <AppShell title="Targets" items={items}>
      <form onSubmit={submit} className="card p-4 flex flex-wrap gap-2 items-end">
        <select className="bg-slate-900 border border-slate-700 rounded-lg p-2" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="domain">domain</option>
          <option value="email">email</option>
          <option value="keyword">keyword</option>
        </select>
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2 min-w-64" value={value} onChange={(e) => setValue(e.target.value)} placeholder="valor" />
        <button className="rounded-lg bg-accent px-4 py-2">Criar target</button>
      </form>
      <DataTable headers={['Tipo', 'Valor', 'Ativo']}>
        {data?.items?.map((t: any) => (
          <tr key={t.id} className="border-t border-slate-800">
            <td className="p-3">{t.type}</td>
            <td className="p-3">{t.value}</td>
            <td className="p-3">{String(t.active)}</td>
          </tr>
        ))}
      </DataTable>
    </AppShell>
  );
}
