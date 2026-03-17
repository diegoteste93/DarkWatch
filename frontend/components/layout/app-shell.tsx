'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useAuthStore } from '@/store/auth';

type Item = { href: string; label: string };

export function AppShell({ title, items, children }: { title: string; items: Item[]; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { me, logout } = useAuthStore();

  return (
    <div className="min-h-screen grid grid-cols-[250px_1fr]">
      <aside className="border-r border-slate-800 p-4 bg-black/20">
        <h1 className="text-xl font-semibold mb-6">DarkWatch</h1>
        <nav className="space-y-2">
          {items.map((item) => (
            <Link key={item.href} href={item.href} className={clsx('block px-3 py-2 rounded-lg', pathname === item.href ? 'bg-accent/20 text-accent' : 'hover:bg-slate-800')}>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">{title}</h2>
          <div className="flex items-center gap-3 text-sm">
            <span>{me?.email}</span>
            <button className="px-3 py-1 rounded-lg bg-slate-800" onClick={() => { logout(); router.push('/login'); }}>Sair</button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
