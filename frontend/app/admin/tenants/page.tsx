'use client';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { AppShell } from '@/components/layout/app-shell';
import { DataTable } from '@/components/tables/data-table';

const items = [
  { href: '/admin', label: 'Dashboard' },
  { href: '/admin/tenants', label: 'Tenants' },
  { href: '/admin/runs', label: 'Runs' }
];

export default function AdminTenants() {
  const { data } = useQuery({ queryKey: ['tenants'], queryFn: async () => (await api.get('/tenants?page=1&page_size=50')).data });

  return (
    <AppShell title="Tenants" items={items}>
      <DataTable headers={['Nome', 'Ações']}>
        {data?.items?.map((t: any) => (
          <tr key={t.id} className="border-t border-slate-800">
            <td className="p-3">{t.name}</td>
            <td className="p-3">Ver detalhes</td>
          </tr>
        ))}
      </DataTable>
    </AppShell>
  );
}
