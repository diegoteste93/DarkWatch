'use client';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function OverviewChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <div className="card p-4 h-72">
      <p className="mb-4">Findings ao longo do tempo</p>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <XAxis dataKey="name" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip />
          <Area type="monotone" dataKey="value" stroke="#06b6d4" fill="#06b6d420" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
