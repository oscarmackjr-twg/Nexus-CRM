import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getContacts } from '@/api/contacts';
import { DataGrid } from '@/components/DataGrid';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';

export default function ContactsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', { page, size }],
    queryFn: () => getContacts({ page, size }),
    placeholderData: (prev) => prev,
  });

  const columns = [
    {
      key: 'name',
      label: 'NAME',
      render: (row) => (
        <Link
          to={`/contacts/${row.id}`}
          className="font-medium text-[#1a3868] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.first_name} {row.last_name}
        </Link>
      ),
    },
    { key: 'company_name', label: 'COMPANY' },
    { key: 'title', label: 'TITLE' },
    {
      key: 'lifecycle_stage',
      label: 'STAGE',
      render: (row) =>
        row.lifecycle_stage ? (
          <Badge variant="secondary">{row.lifecycle_stage}</Badge>
        ) : (
          '\u2014'
        ),
    },
    { key: 'email', label: 'EMAIL' },
    { key: 'lead_score', label: 'SCORE' },
    { key: 'owner_name', label: 'OWNER' },
    {
      key: 'updated_at',
      label: 'UPDATED',
      render: (row) => formatDate(row.updated_at),
    },
  ];

  const handleSort = (key, dir) => {
    setSortKey(key);
    setSortDir(dir);
  };

  const handleSizeChange = (newSize) => {
    setSize(newSize);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Contacts</h1>
      <DataGrid
        columns={columns}
        data={data?.items}
        total={data?.total ?? 0}
        page={data?.page ?? page}
        pages={data?.pages ?? 1}
        size={size}
        isLoading={isLoading}
        onPageChange={setPage}
        onSizeChange={handleSizeChange}
        onRowClick={(row) => navigate(`/contacts/${row.id}`)}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        emptyHeading="No contacts yet"
        emptyBody="Contacts you add will appear here."
      />
    </div>
  );
}
