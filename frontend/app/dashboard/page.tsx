'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import { AppShell } from '@/components/layout/app-shell';
import { MetricCard } from '@/components/cards/metric-card';
import { OverviewChart } from '@/components/charts/overview-chart';
import type { ApiEnvelope, DashboardOverview } from '@/types/api';

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/dashboard/findings', label: 'Findings' },
  { href: '/dashboard/targets', label: 'Targets' },
  { href: '/dashboard/runs', label: 'Runs' },
  { href: '/dashboard/settings', label: 'Settings' }
];

export default function TenantDashboard() {
  const { token, me } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!token) router.push('/login');
  }, [token, router]);

  const tenantId = me?.tenant_id;
  const { data } = useQuery({
    queryKey: ['tenant-overview', tenantId],
    enabled: !!tenantId,
    queryFn: async () => (await api.get<ApiEnvelope<DashboardOverview>>(`/tenants/${tenantId}/dashboard/overview`)).data.data
  });

  return (
    <AppShell title="Security Dashboard" items={items}>
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard label="Total Findings" value={data?.total_findings ?? '-'} />
        <MetricCard label="Novos 24h" value={data?.new_last_24h ?? '-'} />
        <MetricCard label="Total Targets" value={data?.total_targets ?? '-'} />
        <MetricCard label="Último scan" value={data?.last_run_status ?? '-'} />
      </div>
      <OverviewChart data={[{ name: 'Seg', value: 2 }, { name: 'Ter', value: 3 }, { name: 'Qua', value: 5 }, { name: 'Qui', value: 4 }, { name: 'Sex', value: 7 }]} />
    </AppShell>
  );
}
