export function DataTable({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-900/70">
          <tr>{headers.map((h) => <th key={h} className="text-left p-3 font-medium text-slate-300">{h}</th>)}</tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
