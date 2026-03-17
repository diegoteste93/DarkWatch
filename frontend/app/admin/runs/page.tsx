'use client';
import { AppShell } from '@/components/layout/app-shell';

const items = [
  { href: '/admin', label: 'Dashboard' },
  { href: '/admin/tenants', label: 'Tenants' },
  { href: '/admin/runs', label: 'Runs' }
];

export default function AdminRuns() {
  return <AppShell title="Runs (Admin)" items={items}><div className="card p-4">Use o detalhe de tenant para inspeção completa de runs.</div></AppShell>;
}
