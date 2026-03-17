'use client';
import { FormEvent, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { AppShell } from '@/components/layout/app-shell';
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

export default function SettingsPage() {
  const { me } = useAuthStore();
  const tenantId = me?.tenant_id;
  const { data } = useQuery({ queryKey: ['settings', tenantId], enabled: !!tenantId, queryFn: async () => (await api.get(`/tenants/${tenantId}/settings`)).data.data });
  const [form, setForm] = useState<any>({});

  const save = useMutation({
    mutationFn: async () => api.patch(`/tenants/${tenantId}/settings`, form),
    onError: (err: any) => toastError(err?.detail ?? 'Erro ao salvar')
  });

  const test = useMutation({
    mutationFn: async () => api.post(`/tenants/${tenantId}/settings/test-email`),
    onError: (err: any) => toastError(err?.detail ?? 'Falha no teste SMTP')
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate();
  };

  return (
    <AppShell title="Settings" items={items}>
      <form onSubmit={submit} className="card p-4 grid md:grid-cols-2 gap-3">
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2" defaultValue={data?.smtp_host} placeholder="SMTP host" onChange={(e) => setForm((f: any) => ({ ...f, smtp_host: e.target.value }))} />
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2" defaultValue={data?.smtp_port} placeholder="SMTP port" onChange={(e) => setForm((f: any) => ({ ...f, smtp_port: Number(e.target.value) }))} />
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2" defaultValue={data?.smtp_user} placeholder="SMTP user" onChange={(e) => setForm((f: any) => ({ ...f, smtp_user: e.target.value }))} />
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2" placeholder="SMTP password" type="password" onChange={(e) => setForm((f: any) => ({ ...f, smtp_password: e.target.value }))} />
        <input className="bg-slate-900 border border-slate-700 rounded-lg p-2" defaultValue={data?.smtp_from} placeholder="From email" onChange={(e) => setForm((f: any) => ({ ...f, smtp_from: e.target.value }))} />
        <div className="flex gap-2">
          <button className="rounded-lg bg-accent px-4 py-2" type="submit">Salvar</button>
          <button className="rounded-lg bg-slate-700 px-4 py-2" type="button" onClick={() => test.mutate()}>Testar e-mail</button>
        </div>
      </form>
    </AppShell>
  );
}
