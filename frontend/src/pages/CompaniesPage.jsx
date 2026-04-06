import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCompanies } from '@/api/companies';
import { DataGrid } from '@/components/DataGrid';

export default function CompaniesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const { data, isLoading } = useQuery({
    queryKey: ['companies', { page, size }],
    queryFn: () => getCompanies({ page, size }),
    placeholderData: (prev) => prev,
  });

  const columns = [
    {
      key: 'name',
      label: 'NAME',
      render: (row) => (
        <Link
          to={`/companies/${row.id}`}
          className="font-medium text-[#1a3868] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.name}
        </Link>
      ),
    },
    { key: 'company_type_label', label: 'TYPE' },
    { key: 'tier_label', label: 'TIER' },
    { key: 'sector_label', label: 'SECTOR' },
    { key: 'industry', label: 'INDUSTRY' },
    {
      key: 'linked_contacts_count',
      label: 'CONTACTS',
      render: (row) => row.linked_contacts_count ?? 0,
    },
    {
      key: 'open_deals_count',
      label: 'DEALS',
      render: (row) => row.open_deals_count ?? 0,
    },
    { key: 'owner_name', label: 'OWNER' },
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
      <h1 className="text-xl font-semibold">Companies</h1>
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
        onRowClick={(row) => navigate(`/companies/${row.id}`)}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        emptyHeading="No companies yet"
        emptyBody="Companies you add will appear here."
      />
    </div>
  );
}
