'use client';
import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import type { ApiEnvelope } from '@/types/api';
import { toastError } from '@/hooks/use-toast';

export default function LoginPage() {
  const [email, setEmail] = useState('admin@darkwatch.local');
  const [password, setPassword] = useState('Admin123!');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { token, setToken } = useAuthStore();

  useEffect(() => {
    if (token) router.push('/admin');
  }, [token, router]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const { data } = await api.post<ApiEnvelope<{ access_token: string }>>('/auth/login', { email, password });
      setToken(data.data.access_token);
      const me = await api.get('/auth/me', { headers: { Authorization: `Bearer ${data.data.access_token}` } });
      router.push(me.data.data.role === 'ADMIN' ? '/admin' : '/dashboard');
    } catch (err: any) {
      toastError(err?.detail ?? 'Falha no login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <form onSubmit={onSubmit} className="card w-full max-w-md p-6 space-y-4">
        <h1 className="text-2xl font-semibold">DarkWatch Login</h1>
        <input className="w-full rounded-lg bg-slate-900 border border-slate-700 p-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        <input className="w-full rounded-lg bg-slate-900 border border-slate-700 p-2" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="senha" type="password" />
        <button className="w-full rounded-lg bg-accent hover:bg-cyan transition py-2 font-medium" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
      </form>
    </div>
  );
}
