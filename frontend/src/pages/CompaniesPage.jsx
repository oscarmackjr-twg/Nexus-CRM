import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCompanies } from '@/api/companies';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function CompaniesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['companies', page],
    queryFn: () => getCompanies({ page, size: 25 }),
  });

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>;
  if (isError) return <div className="p-6 text-red-600">Failed to load companies.</div>;

  const { items = [], total = 0, pages = 1 } = data || {};

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Companies</h1>
        <span className="text-sm text-muted-foreground">{total} total</span>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Name</th>
              <th className="text-left px-4 py-3 font-medium">Industry</th>
              <th className="text-left px-4 py-3 font-medium">Size</th>
              <th className="text-left px-4 py-3 font-medium">Revenue</th>
              <th className="text-left px-4 py-3 font-medium">Owner</th>
              <th className="text-left px-4 py-3 font-medium">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((c) => (
              <tr key={c.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/companies/${c.id}`} className="font-medium text-primary hover:underline">
                    {c.name}
                  </Link>
                  {c.domain && (
                    <div className="text-xs text-muted-foreground">{c.domain}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{c.industry || '—'}</td>
                <td className="px-4 py-3 text-muted-foreground">{c.size_range || '—'}</td>
                <td className="px-4 py-3">{formatCurrency(c.annual_revenue)}</td>
                <td className="px-4 py-3 text-muted-foreground">{c.owner_name || '—'}</td>
                <td className="px-4 py-3 text-muted-foreground">{formatDate(c.created_at)}</td>
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
