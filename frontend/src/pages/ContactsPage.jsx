import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getContacts } from '@/api/contacts';
import { formatDate } from '@/lib/utils';

export default function ContactsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['contacts', page],
    queryFn: () => getContacts({ page, size: 25 }),
  });

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>;
  if (isError) return <div className="p-6 text-red-600">Failed to load contacts.</div>;

  const { items = [], total = 0, pages = 1 } = data || {};

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Contacts</h1>
        <span className="text-sm text-muted-foreground">{total} total</span>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Name</th>
              <th className="text-left px-4 py-3 font-medium">Title</th>
              <th className="text-left px-4 py-3 font-medium">Company</th>
              <th className="text-left px-4 py-3 font-medium">Email</th>
              <th className="text-left px-4 py-3 font-medium">Owner</th>
              <th className="text-left px-4 py-3 font-medium">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((c) => (
              <tr key={c.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/contacts/${c.id}`} className="font-medium text-primary hover:underline">
                    {c.first_name} {c.last_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{c.title || '—'}</td>
                <td className="px-4 py-3">{c.company_name || '—'}</td>
                <td className="px-4 py-3 text-muted-foreground">{c.email || '—'}</td>
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
