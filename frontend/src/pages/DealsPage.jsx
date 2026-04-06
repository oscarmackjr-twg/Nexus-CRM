import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getDeals } from '@/api/deals';
import { formatCurrency, formatDate } from '@/lib/utils';

const STATUS_COLORS = {
  open: 'bg-blue-100 text-blue-700',
  won: 'bg-green-100 text-green-700',
  lost: 'bg-red-100 text-red-700',
};

export default function DealsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['deals', page],
    queryFn: () => getDeals({ page, size: 25 }),
  });

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>;
  if (isError) return <div className="p-6 text-red-600">Failed to load deals.</div>;

  const { items = [], total = 0, pages = 1 } = data || {};

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Deals</h1>
        <span className="text-sm text-muted-foreground">{total} total</span>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Deal</th>
              <th className="text-left px-4 py-3 font-medium">Stage</th>
              <th className="text-left px-4 py-3 font-medium">Value</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Company</th>
              <th className="text-left px-4 py-3 font-medium">Close Date</th>
              <th className="text-left px-4 py-3 font-medium">Owner</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((d) => (
              <tr key={d.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/deals/${d.id}`} className="font-medium text-primary hover:underline">
                    {d.name}
                  </Link>
                  <div className="text-xs text-muted-foreground">{d.pipeline_name}</div>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{d.stage_name}</td>
                <td className="px-4 py-3 font-medium">{formatCurrency(d.value, d.currency)}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[d.status] || 'bg-gray-100 text-gray-700'}`}>
                    {d.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{d.company_name || '—'}</td>
                <td className="px-4 py-3 text-muted-foreground">{formatDate(d.expected_close_date)}</td>
                <td className="px-4 py-3 text-muted-foreground">{d.owner_name || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex items-center gap-2">
          <button
            className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">Page {page} of {pages}</span>
          <button
            className="px-3 py-1 rounded border text-sm disabled:opacity-40"
            disabled={page === pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
