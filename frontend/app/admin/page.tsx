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
  { href: '/admin', label: 'Dashboard' },
  { href: '/admin/tenants', label: 'Tenants' },
  { href: '/admin/runs', label: 'Runs' }
];

export default function AdminHome() {
  const { token, me } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!token) router.push('/login');
    if (me && me.role !== 'ADMIN') router.push('/dashboard');
  }, [token, me, router]);

  const { data } = useQuery({
    queryKey: ['admin-overview'],
    queryFn: async () => (await api.get<ApiEnvelope<DashboardOverview>>('/admin/dashboard/overview')).data.data,
    enabled: !!token
  });

  return (
    <AppShell title="Admin Dashboard" items={items}>
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard label="Total Findings" value={data?.total_findings ?? '-'} />
        <MetricCard label="Novos 24h" value={data?.new_last_24h ?? '-'} />
        <MetricCard label="Total Targets" value={data?.total_targets ?? '-'} />
        <MetricCard label="Runs com falha" value={data?.failed_runs ?? '-'} />
      </div>
      <OverviewChart data={[{ name: 'D-6', value: 3 }, { name: 'D-5', value: 6 }, { name: 'D-4', value: 4 }, { name: 'D-3', value: 8 }, { name: 'D-2', value: 7 }, { name: 'D-1', value: 10 }]} />
    </AppShell>
  );
}
